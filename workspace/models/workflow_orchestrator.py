#!/usr/bin/env python3

import json
import time
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from .planner_llm import PlannerLLM
from .judge_llm import JudgeLLM

@dataclass
class IterationResult:
    """Results from a single iteration of the planning-judging cycle"""
    iteration: int
    planner_output: List[str]
    judge_feedback: Dict[str, Any]
    converged: bool
    changes_made: bool

@dataclass
class WorkflowResult:
    """Complete results from the planning-judging workflow"""
    initial_actions: List[str]
    final_actions: List[str]
    goal: str
    planner_name: str
    judge_name: str
    iterations: List[IterationResult]
    total_iterations: int
    converged: bool
    execution_time: float

class WorkflowOrchestrator:
    """Orchestrates the iterative planning-judging workflow"""
    
    def __init__(self, max_iterations: int = 5, convergence_threshold: int = 2):
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
    
    def run_workflow(self, 
                     initial_actions: List[str], 
                     planner: PlannerLLM, 
                     judge: JudgeLLM,
                     context: str = "") -> WorkflowResult:
        """
        Run the complete planning-judging workflow:
        1. Planner annotates goal
        2. Judge provides feedback
        3. Planner modifies plan
        4. Repeat until convergence
        """
        start_time = time.time()
        
        # Step 1: Initial goal annotation by planner
        goal = planner.annotate_goal(initial_actions, context)
        print(f"Goal identified: {goal}")
        
        current_actions = initial_actions.copy()
        iterations = []
        stable_iterations = 0
        
        for iteration in range(self.max_iterations):
            print(f"\n--- Iteration {iteration + 1} ---")
            
            # Step 2: Judge evaluates current plan
            judge_feedback = judge.judge_plan(current_actions, goal)
            
            # Check if judge found any issues
            has_changes = judge_feedback.get('has_changes', False)
            
            if not has_changes:
                stable_iterations += 1
                print(f"No changes suggested by judge (stable: {stable_iterations}/{self.convergence_threshold})")
            else:
                stable_iterations = 0
                print(f"Judge suggested changes: {len(judge_feedback.get('remove_actions', []))} removals, "
                      f"{len(judge_feedback.get('missing_requirements', []))} missing requirements")
            
            # Step 3: Planner modifies plan based on feedback
            if has_changes:
                modified_actions = planner.modify_plan(
                    current_actions, 
                    judge_feedback['raw_response'], 
                    goal
                )
                changes_made = modified_actions != current_actions
                current_actions = modified_actions
            else:
                changes_made = False
            
            # Record iteration results
            iteration_result = IterationResult(
                iteration=iteration + 1,
                planner_output=current_actions.copy(),
                judge_feedback=judge_feedback,
                converged=stable_iterations >= self.convergence_threshold,
                changes_made=changes_made
            )
            iterations.append(iteration_result)
            
            # Check for convergence
            if stable_iterations >= self.convergence_threshold:
                print(f"Converged after {iteration + 1} iterations")
                break
        
        execution_time = time.time() - start_time
        
        return WorkflowResult(
            initial_actions=initial_actions,
            final_actions=current_actions,
            goal=goal,
            planner_name=str(planner),
            judge_name=str(judge),
            iterations=iterations,
            total_iterations=len(iterations),
            converged=stable_iterations >= self.convergence_threshold,
            execution_time=execution_time
        )
    
    def run_cross_validation(self, 
                           initial_actions: List[str],
                           planners: Dict[str, PlannerLLM],
                           judges: Dict[str, JudgeLLM],
                           context: str = "") -> Dict[str, Dict[str, WorkflowResult]]:
        """
        Run all combinations of planners and judges
        Returns: {planner_name: {judge_name: WorkflowResult}}
        """
        results = {}
        total_combinations = len(planners) * len(judges)
        current_combination = 0
        
        for planner_name, planner in planners.items():
            results[planner_name] = {}
            
            for judge_name, judge in judges.items():
                current_combination += 1
                print(f"\n{'='*60}")
                print(f"Running combination {current_combination}/{total_combinations}: "
                      f"{planner_name} + {judge_name}")
                print(f"{'='*60}")
                
                try:
                    result = self.run_workflow(initial_actions, planner, judge, context)
                    results[planner_name][judge_name] = result
                    
                    print(f"Completed: {result.total_iterations} iterations, "
                          f"Converged: {result.converged}, "
                          f"Time: {result.execution_time:.2f}s")
                    
                except Exception as e:
                    print(f"Error in combination {planner_name} + {judge_name}: {e}")
                    # Create error result
                    results[planner_name][judge_name] = WorkflowResult(
                        initial_actions=initial_actions,
                        final_actions=[],
                        goal="ERROR",
                        planner_name=planner_name,
                        judge_name=judge_name,
                        iterations=[],
                        total_iterations=0,
                        converged=False,
                        execution_time=0.0
                    )
                
                # Add delay between combinations to respect rate limits
                time.sleep(2)
        
        return results
    
    def save_results(self, results: Dict[str, Dict[str, WorkflowResult]], filename: str):
        """Save workflow results to JSON file"""
        # Convert results to serializable format
        serializable_results = {}
        
        for planner_name, planner_results in results.items():
            serializable_results[planner_name] = {}
            
            for judge_name, result in planner_results.items():
                serializable_results[planner_name][judge_name] = {
                    'initial_actions': result.initial_actions,
                    'final_actions': result.final_actions,
                    'goal': result.goal,
                    'planner_name': result.planner_name,
                    'judge_name': result.judge_name,
                    'total_iterations': result.total_iterations,
                    'converged': result.converged,
                    'execution_time': result.execution_time,
                    'iterations': [
                        {
                            'iteration': it.iteration,
                            'planner_output': it.planner_output,
                            'judge_feedback': it.judge_feedback,
                            'converged': it.converged,
                            'changes_made': it.changes_made
                        }
                        for it in result.iterations
                    ]
                }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"Results saved to {filename}")
    
    def generate_summary_report(self, results: Dict[str, Dict[str, WorkflowResult]]) -> str:
        """Generate a summary report of all workflow results"""
        report = []
        report.append("WORKFLOW ORCHESTRATOR SUMMARY REPORT")
        report.append("=" * 50)
        report.append("")
        
        # Overall statistics
        total_workflows = sum(len(judges) for judges in results.values())
        converged_workflows = sum(
            1 for planner_results in results.values()
            for result in planner_results.values()
            if result.converged
        )
        
        report.append(f"Total workflows executed: {total_workflows}")
        report.append(f"Converged workflows: {converged_workflows} ({converged_workflows/total_workflows*100:.1f}%)")
        report.append("")
        
        # Per-combination results
        report.append("DETAILED RESULTS:")
        report.append("-" * 30)
        
        for planner_name, planner_results in results.items():
            report.append(f"\nPlanner: {planner_name}")
            
            for judge_name, result in planner_results.items():
                report.append(f"  + Judge: {judge_name}")
                report.append(f"    Iterations: {result.total_iterations}")
                report.append(f"    Converged: {result.converged}")
                report.append(f"    Time: {result.execution_time:.2f}s")
                report.append(f"    Final actions: {len(result.final_actions)}")
                report.append("")
        
        return "\n".join(report)