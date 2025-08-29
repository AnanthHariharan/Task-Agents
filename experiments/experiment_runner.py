#!/usr/bin/env python3

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from planning_agent.factory import PlannerFactory
from judge_llm.factory import JudgeFactory
from shared.workflow.orchestrator import WorkflowOrchestrator
from shared.utils.file_utils import FileManager
from shared.utils.logging_utils import setup_logging, LoggerMixin

class ExperimentRunner(LoggerMixin):
    """Main experiment framework for cross-model comparisons"""
    def __init__(self,
                 data_path: str = "data/processed/seq_shortest.json",
                 output_dir: str = "outputs/experiments"):
        self.data_path = data_path
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.logger = setup_logging(log_dir="logs")
        FileManager.ensure_dir(output_dir)
        self.orchestrator = WorkflowOrchestrator(max_iterations=5, convergence_threshold=2)

    def load_test_data(self, max_samples: int = 10) -> List[Dict[str, Any]]:
        self.logger.info(f"Loading test data from {self.data_path}")

        try:
            data = FileManager.load_json(self.data_path)
        except Exception as e:
            self.logger.error(f"Failed to load test data: {e}")
            return []

        if max_samples > 0:
            data = data[:max_samples]

        self.logger.info(f"Loaded {len(data)} test sequences")
        return data

    def run_full_experiment(self, max_samples: int = 10, test_mode: bool = True, evaluation_mode: str = "iterative") -> str:
        self.logger.info(f"Starting experiment at {datetime.now()}")
        self.logger.info(f"Results will be saved to: {self.output_dir}")

        test_data = self.load_test_data(max_samples)
        if not test_data:
            self.logger.error("No test data loaded, aborting experiment")
            return self.output_dir

        self.logger.info("Initializing models...")
        try:
            planners = PlannerFactory.create_all_planners(include_rule_based=True, temperature=0.3, max_tokens=512)
            judges = JudgeFactory.create_all_judges(include_rule_based=True, temperature=0.3, max_tokens=512)

            self.logger.info(f"Created {len(planners)} planners: {list(planners.keys())}")
            self.logger.info(f"Created {len(judges)} judges: {list(judges.keys())}")
        except Exception as e:
            self.logger.error(f"Error creating models: {e}")
            return self.output_dir

        if evaluation_mode == "one_shot":
            all_results = self._run_one_shot_experiment(test_data, planners, judges, test_mode)
        else:
            all_results = self._run_iterative_experiment(test_data, planners, judges, test_mode)

        results_file = self._save_final_results(all_results)
        self._generate_analysis(all_results)

        self.logger.info("Experiment completed!")
        self.logger.info(f"Results saved to: {results_file}")

        return self.output_dir

    def _run_iterative_experiment(self, test_data: List[Dict], planners: Dict, judges: Dict, test_mode: bool) -> Dict:
        """Run iterative workflow experiment"""
        all_results = {}

        for i, test_sequence in enumerate(test_data):
            sequence_id = f"seq_{i:03d}"
            actions = test_sequence.get('actions', [])
            file_name = test_sequence.get('file', 'unknown')

            self.logger.info(f"Processing sequence {i+1}/{len(test_data)}: {sequence_id}")
            self.logger.info(f"File: {file_name}")
            self.logger.info(f"Initial actions: {len(actions)}")

            if test_mode:
                test_planners = {list(planners.keys())[0]: list(planners.values())[0]}
                test_judges = {list(judges.keys())[0]: list(judges.values())[0]}
            else:
                test_planners = planners
                test_judges = judges

            sequence_results = self.orchestrator.run_cross_validation(
                actions, test_planners, test_judges, context=file_name
            )

            all_results[sequence_id] = {
                'file': file_name,
                'initial_actions': actions,
                'results': sequence_results
            }

            self._save_intermediate_results(all_results, sequence_id)

        return all_results

    def _run_one_shot_experiment(self, test_data: List[Dict], planners: Dict, judges: Dict, test_mode: bool) -> Dict:
        """Run one-shot evaluation experiment (matching paper's Table 1)"""
        from experiments.one_shot_evaluator import OneShotEvaluator

        self.logger.info("Running one-shot evaluation experiment")

        if test_mode:
            test_planners = {list(planners.keys())[0]: list(planners.values())[0]}
            test_judges = {list(judges.keys())[0]: list(judges.values())[0]}
        else:
            test_planners = planners
            test_judges = judges

        evaluator = OneShotEvaluator(output_dir=os.path.join(self.output_dir, "one_shot"))

        raw_results = evaluator.evaluate_raw_teach_plans(test_data, test_judges)


        matrix_results = evaluator.evaluate_planner_judge_matrix(test_data, test_planners, test_judges)


        tables = evaluator.generate_paper_tables(raw_results, matrix_results)


        tables_dir = os.path.join(self.output_dir, "latex_tables")
        FileManager.ensure_dir(tables_dir)

        for table_name, table_latex in tables.items():
            table_file = os.path.join(tables_dir, f"{table_name}_{self.timestamp}.tex")
            FileManager.save_text(table_latex, table_file)
            self.logger.info(f"Saved LaTeX table: {table_file}")


        all_results = self._convert_one_shot_to_analysis_format(raw_results, matrix_results, test_data)

        return all_results

    def _convert_one_shot_to_analysis_format(self, raw_results: Dict, matrix_results: Dict, test_data: List[Dict]) -> Dict:
        """Convert one-shot results to analysis format"""
        all_results = {}


        for i, test_sequence in enumerate(test_data):
            sequence_id = f"seq_{i:03d}"
            actions = test_sequence.get('actions', [])
            file_name = test_sequence.get('file', 'unknown')

            all_results[sequence_id] = {
                'file': file_name,
                'initial_actions': actions,
                'results': {},
                'evaluation_mode': 'one_shot',
                'raw_results': raw_results,
                'matrix_results': matrix_results
            }

        return all_results

    def _save_intermediate_results(self, all_results: Dict, sequence_id: str):
        """Save intermediate results after each sequence"""
        filename = os.path.join(self.output_dir, "runs", f"intermediate_results_{self.timestamp}.json")


        serializable_results = self._convert_to_serializable(all_results)

        FileManager.save_json(serializable_results, filename)
        self.logger.debug(f"Saved intermediate results for {sequence_id}")

    def _save_final_results(self, all_results: Dict) -> str:
        """Save final comprehensive results"""
        filename = os.path.join(self.output_dir, "runs", f"full_results_{self.timestamp}.json")


        serializable_results = self._convert_to_serializable(all_results)

        FileManager.save_json(serializable_results, filename)
        self.logger.info(f"Saved final results to {filename}")

        return filename

    def _convert_to_serializable(self, results: Dict) -> Dict:
        """Convert workflow results to JSON-serializable format"""
        serializable = {}

        for seq_id, seq_data in results.items():
            serializable[seq_id] = {
                'file': seq_data['file'],
                'initial_actions': seq_data['initial_actions'],
                'results': {}
            }

            for planner_name, planner_results in seq_data['results'].items():
                serializable[seq_id]['results'][planner_name] = {}

                for judge_name, workflow_result in planner_results.items():
                    serializable[seq_id]['results'][planner_name][judge_name] = {
                        'initial_actions': workflow_result.initial_actions,
                        'final_actions': workflow_result.final_actions,
                        'goal': workflow_result.goal,
                        'planner_name': workflow_result.planner_name,
                        'judge_name': workflow_result.judge_name,
                        'total_iterations': workflow_result.total_iterations,
                        'converged': workflow_result.converged,
                        'execution_time': workflow_result.execution_time,
                        'iterations': [
                            {
                                'iteration': it.iteration,
                                'planner_output': it.planner_output,
                                'judge_feedback': it.judge_feedback,
                                'converged': it.converged,
                                'changes_made': it.changes_made
                            }
                            for it in workflow_result.iterations
                        ]
                    }

        return serializable

    def _generate_analysis(self, all_results: Dict):
        """Generate comprehensive analysis and visualizations"""
        self.logger.info("Generating analysis...")


        try:
            import pandas as pd
            import matplotlib.pyplot as plt
            import seaborn as sns
        except ImportError:
            self.logger.warning("Analysis libraries not available, skipping visualizations")
            return


        metrics_data = []

        for seq_id, seq_data in all_results.items():
            for planner_name, planner_results in seq_data['results'].items():
                for judge_name, result in planner_results.items():
                    metrics_data.append({
                        'sequence_id': seq_id,
                        'planner': planner_name,
                        'judge': judge_name,
                        'initial_actions': len(result.initial_actions),
                        'final_actions': len(result.final_actions),
                        'iterations': result.total_iterations,
                        'converged': result.converged,
                        'execution_time': result.execution_time,
                        'actions_added': len(result.final_actions) - len(result.initial_actions),
                        'file': seq_data['file']
                    })


        df = pd.DataFrame(metrics_data)


        csv_file = os.path.join(self.output_dir, "analysis", f"metrics_{self.timestamp}.csv")
        FileManager.ensure_dir(os.path.dirname(csv_file))
        df.to_csv(csv_file, index=False)
        self.logger.info(f"Metrics saved to: {csv_file}")


        self._create_visualizations(df)


        self._generate_summary_report(df)

    def _create_visualizations(self, df):
        """Create analysis visualizations"""
        try:
            import matplotlib.pyplot as plt
            import seaborn as sns

            plt.style.use('default')
            fig, axes = plt.subplots(2, 3, figsize=(18, 12))
            fig.suptitle('Multi-Model Plan Verification Analysis', fontsize=16)


            convergence_pivot = df.pivot_table(
                values='converged',
                index='planner',
                columns='judge',
                aggfunc='mean'
            )
            sns.heatmap(convergence_pivot, annot=True, fmt='.2f',
                       cmap='RdYlGn', ax=axes[0,0])
            axes[0,0].set_title('Convergence Rate by Model Combination')


            iterations_pivot = df.pivot_table(
                values='iterations',
                index='planner',
                columns='judge',
                aggfunc='mean'
            )
            sns.heatmap(iterations_pivot, annot=True, fmt='.1f',
                       cmap='RdYlBu_r', ax=axes[0,1])
            axes[0,1].set_title('Average Iterations by Model Combination')


            time_pivot = df.pivot_table(
                values='execution_time',
                index='planner',
                columns='judge',
                aggfunc='mean'
            )
            sns.heatmap(time_pivot, annot=True, fmt='.1f',
                       cmap='plasma', ax=axes[0,2])
            axes[0,2].set_title('Average Execution Time (s)')


            df['actions_change'] = df['final_actions'] - df['initial_actions']
            sns.boxplot(data=df, x='planner', y='actions_change', ax=axes[1,0])
            axes[1,0].set_title('Action Count Changes by Planner')
            axes[1,0].tick_params(axis='x', rotation=45)


            planner_convergence = df.groupby('planner')['converged'].mean()
            planner_convergence.plot(kind='bar', ax=axes[1,1])
            axes[1,1].set_title('Convergence Rate by Planner')
            axes[1,1].tick_params(axis='x', rotation=45)


            judge_convergence = df.groupby('judge')['converged'].mean()
            judge_convergence.plot(kind='bar', ax=axes[1,2])
            axes[1,2].set_title('Convergence Rate by Judge')
            axes[1,2].tick_params(axis='x', rotation=45)

            plt.tight_layout()


            plot_file = os.path.join(self.output_dir, "visualizations", f"analysis_{self.timestamp}.png")
            FileManager.ensure_dir(os.path.dirname(plot_file))
            plt.savefig(plot_file, dpi=300, bbox_inches='tight')
            plt.close()

            self.logger.info(f"Visualizations saved to: {plot_file}")

        except Exception as e:
            self.logger.error(f"Error creating visualizations: {e}")

    def _generate_summary_report(self, df):
        """Generate a comprehensive summary report"""
        report_file = os.path.join(self.output_dir, "analysis", f"summary_report_{self.timestamp}.txt")
        FileManager.ensure_dir(os.path.dirname(report_file))

        report_content = f"""MULTI-MODEL PLAN VERIFICATION EXPERIMENT REPORT
{'=' * 60}

Experiment Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Total Workflows: {len(df)}
Unique Sequences: {df['sequence_id'].nunique()}
Model Combinations: {df['planner'].nunique()} × {df['judge'].nunique()}

OVERALL PERFORMANCE
{'-' * 30}
Average Convergence Rate: {df['converged'].mean():.2%}
Average Iterations: {df['iterations'].mean():.1f}
Average Execution Time: {df['execution_time'].mean():.1f}s
Average Actions Added: {df['actions_added'].mean():.1f}

TOP PERFORMING COMBINATIONS
{'-' * 30}
"""


        combo_performance = df.groupby(['planner', 'judge']).agg({
            'converged': 'mean',
            'iterations': 'mean',
            'execution_time': 'mean'
        }).round(2)


        combo_performance['score'] = (
            combo_performance['converged'] * 100 -
            combo_performance['iterations'] * 2
        )

        top_combos = combo_performance.sort_values('score', ascending=False).head(5)

        for i, ((planner, judge), row) in enumerate(top_combos.iterrows(), 1):
            report_content += f"""{i}. {planner} + {judge}
   Convergence: {row['converged']:.2%}
   Avg Iterations: {row['iterations']:.1f}
   Avg Time: {row['execution_time']:.1f}s

"""

        FileManager.save_text(report_content, report_file)
        self.logger.info(f"Summary report saved to: {report_file}")

def main():
    """Main function to run experiments"""
    import argparse

    parser = argparse.ArgumentParser(description='Run multi-model plan verification experiments')
    parser.add_argument('--samples', type=int, default=5, help='Number of test sequences')
    parser.add_argument('--test-mode', action='store_true', help='Run in test mode (fewer combinations)')
    parser.add_argument('--evaluation-mode', choices=['iterative', 'one_shot'], default='iterative',
                       help='Evaluation mode: iterative (full workflow) or one_shot (direct evaluation)')
    parser.add_argument('--data-path', default='data/processed/seq_shortest.json', help='Path to test data')
    parser.add_argument('--output-dir', default='outputs/experiments', help='Output directory')

    args = parser.parse_args()


    runner = ExperimentRunner(
        data_path=args.data_path,
        output_dir=args.output_dir
    )


    results_dir = runner.run_full_experiment(
        max_samples=args.samples,
        test_mode=args.test_mode,
        evaluation_mode=args.evaluation_mode
    )

    print(f"\nExperiment completed successfully!")
    print(f"All results available in: {results_dir}")

if __name__ == "__main__":
    main()
