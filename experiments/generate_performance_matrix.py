import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from experiments.one_shot_evaluator import OneShotEvaluator
from planning_agent.factory import PlannerFactory
from judge_llm.factory import JudgeFactory
from shared.utils.file_utils import FileManager
from shared.utils.logging_utils import setup_logging, LoggerMixin

class PerformanceMatrixGenerator(LoggerMixin):
    def __init__(self, output_dir: str = "outputs/performance_matrices"):
        self.output_dir = output_dir
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")


        self.logger = setup_logging(log_dir="logs")


        FileManager.ensure_dir(output_dir)

    def generate_all_matrices(self,
                            test_data_path: str = "data/processed/seq_shortest.json",
                            max_samples: int = 50) -> str:
        """Generate all performance matrices (Tables 1, 2, 3 from your paper)"""

        self.logger.info("Generating performance matrices for paper")


        test_data = FileManager.load_json(test_data_path)
        if max_samples > 0:
            test_data = test_data[:max_samples]

        self.logger.info(f"Loaded {len(test_data)} test sequences")


        self.logger.info("Creating all model instances...")
        planners = PlannerFactory.create_all_planners(include_rule_based=True)
        judges = JudgeFactory.create_all_judges(include_rule_based=True)
        self.logger.info(f"Created {len(planners)} planners: {list(planners.keys())}")
        self.logger.info(f"Created {len(judges)} judges: {list(judges.keys())}")
        evaluator = OneShotEvaluator(output_dir=os.path.join(self.output_dir, "evaluations"))
        self.logger.info("Generating Table 1: Raw TEACh Plan Evaluation...")
        raw_results = evaluator.evaluate_raw_teach_plans(test_data, judges)
        self.logger.info("Generating Tables 2 & 3: 4x4 Planner-Judge Matrix...")
        matrix_results = evaluator.evaluate_planner_judge_matrix(test_data, planners, judges)


        self.logger.info("Generating LaTeX tables...")
        tables = evaluator.generate_paper_tables(raw_results, matrix_results)


        results_dir = os.path.join(self.output_dir, f"paper_tables_{self.timestamp}")
        FileManager.ensure_dir(results_dir)


        FileManager.save_json(raw_results, os.path.join(results_dir, "table1_raw_data.json"))
        FileManager.save_json(matrix_results, os.path.join(results_dir, "tables23_matrix_data.json"))


        for table_name, table_latex in tables.items():
            table_file = os.path.join(results_dir, f"{table_name}.tex")
            FileManager.save_text(table_latex, table_file)
            self.logger.info(f"Saved LaTeX table: {table_file}")


        self._generate_tables_summary(raw_results, matrix_results, results_dir)

        self.logger.info(f"All performance matrices generated successfully!")
        self.logger.info(f"Results available in: {results_dir}")

        return results_dir

    def _generate_tables_summary(self,
                               raw_results: Dict[str, Any],
                               matrix_results: Dict[str, Dict[str, Any]],
                               output_dir: str):
        """Generate a summary of all tables for the paper"""

        summary = []
        summary.append("PERFORMANCE MATRICES FOR PAPER")
        summary.append("=" * 50)
        summary.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        summary.append("")


        if raw_results:
            summary.append("TABLE 1: Judge LLM Performance on Raw TEACh Plans")
            summary.append("-" * 50)
            summary.append("Judge LLM           | Recall (%) | Precision (%)")
            summary.append("-" * 50)

            for judge_name, results in raw_results.items():
                metrics = results['aggregated_metrics']
                display_name = self._format_judge_name(judge_name)
                summary.append(f"{display_name:18} | {metrics.recall*100:8.0f}   | {metrics.precision*100:10.0f}")

            summary.append("")


        if matrix_results:
            summary.append("TABLES 2 & 3: 4x4 Planner-Judge Matrix Summary")
            summary.append("-" * 50)


            all_recall = []
            all_precision = []

            for planner_name, judge_results in matrix_results.items():
                planner_recalls = []
                planner_precisions = []

                for judge_name, results in judge_results.items():
                    metrics = results['aggregated_metrics']
                    planner_recalls.append(metrics.recall)
                    planner_precisions.append(metrics.precision)

                avg_recall = sum(planner_recalls) / len(planner_recalls) if planner_recalls else 0
                avg_precision = sum(planner_precisions) / len(planner_precisions) if planner_precisions else 0

                display_name = self._format_judge_name(planner_name)
                summary.append(f"{display_name:18} Planner | Avg Recall: {avg_recall*100:5.0f}% | Avg Precision: {avg_precision*100:5.0f}%")

                all_recall.extend(planner_recalls)
                all_precision.extend(planner_precisions)


            if all_recall and all_precision:
                summary.append("")
                summary.append(f"{'Overall Average':18} | Recall: {sum(all_recall)/len(all_recall)*100:8.0f}% | Precision: {sum(all_precision)/len(all_precision)*100:8.0f}%")


        summary.append("")
        summary.append("USAGE INSTRUCTIONS")
        summary.append("-" * 30)
        summary.append("1. Copy the LaTeX code from the .tex files into your paper")
        summary.append("2. Make sure to include \\usepackage{booktabs} in your LaTeX preamble")
        summary.append("3. Adjust table captions and labels as needed")
        summary.append("4. The raw JSON data is available for further analysis")


        summary_text = "\\n".join(summary)
        FileManager.save_text(summary_text, os.path.join(output_dir, "tables_summary.txt"))


        self.logger.info("Key Performance Summary:")
        for line in summary:
            if "Judge LLM" in line or "Planner" in line or "Overall Average" in line:
                self.logger.info(line)

    def _format_judge_name(self, judge_name: str) -> str:
        """Format judge name for paper display"""
        name_mapping = {
            'openai': 'GPT-4o-mini',
            'deepseek': 'DeepSeek-R1',
            'gemini': 'Gemini 2.5 Flash',
            'llama': 'LLaMA 4 Scout',
            'rule_based': 'Rule-based'
        }
        return name_mapping.get(judge_name, judge_name)

def main():
    """Main function for generating performance matrices"""
    import argparse

    parser = argparse.ArgumentParser(description='Generate performance matrices for paper')
    parser.add_argument('--data-path', default='data/processed/seq_shortest.json',
                       help='Path to test data')
    parser.add_argument('--samples', type=int, default=50,
                       help='Number of test sequences')
    parser.add_argument('--output-dir', default='outputs/performance_matrices',
                       help='Output directory')

    args = parser.parse_args()

    generator = PerformanceMatrixGenerator(output_dir=args.output_dir)
    results_dir = generator.generate_all_matrices(
        test_data_path=args.data_path,
        max_samples=args.samples
    )

    print(f"\\nPerformance matrices generated successfully!")
    print(f"LaTeX tables and data available in: {results_dir}")
    print(f"\\nTo use in your paper:")
    print(f"1. Copy LaTeX code from the .tex files")
    print(f"2. Include \\\\usepackage{{booktabs}} in your preamble")
    print(f"3. Adjust captions and labels as needed")

if __name__ == "__main__":
    main()
