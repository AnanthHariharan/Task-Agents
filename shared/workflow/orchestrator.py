#!/usr/bin/env python3

import time
from typing import List, Dict, Any
from dataclasses import dataclass
from planning_agent import BasePlanner
from judge_llm import BaseJudge
from shared.utils.logging_utils import LoggerMixin

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

class WorkflowOrchestrator(LoggerMixin):
    """Orchestrates the iterative planning-judging workflow"""
    
    def __init__(self, max_iterations: int = 5, convergence_threshold: int = 2):
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
    
    def run_workflow(self, 
                     initial_actions: List[str], 
                     planner: BasePlanner, 
                     judge: BaseJudge,
                     context: str = "") -> WorkflowResult:
        """
        Run the complete planning-judging workflow:
        1. Planner annotates goal
        2. Judge provides feedback
        3. Planner modifies plan
        4. Repeat until convergence
        """
        start_time = time.time()
        
        self.logger.info(f"Starting workflow: {planner} + {judge}")
        
        # Step 1: Initial goal annotation by planner
        goal = planner.annotate_goal(initial_actions, context)
        self.logger.info(f"Goal identified: {goal}")
        
        current_actions = initial_actions.copy()
        iterations = []
        stable_iterations = 0
        
        for iteration in range(self.max_iterations):
            self.logger.info(f"--- Iteration {iteration + 1} ---")
            
            # Step 2: Judge evaluates current plan
            judge_feedback = judge.judge_plan(current_actions, goal)
            
            # Check if judge found any issues
            has_changes = judge_feedback.get('has_changes', False)
            
            if not has_changes:
                stable_iterations += 1
                self.logger.info(f"No changes suggested (stable: {stable_iterations}/{self.convergence_threshold})")
            else:
                stable_iterations = 0
                self.logger.info(f"Judge suggested changes: {len(judge_feedback.get('remove_actions', []))} removals, "
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
                self.logger.info(f"Converged after {iteration + 1} iterations")
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
                           planners: Dict[str, BasePlanner],
                           judges: Dict[str, BaseJudge],
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
                self.logger.info(f"Running combination {current_combination}/{total_combinations}: "
                      f"{planner_name} + {judge_name}")
                
                try:
                    result = self.run_workflow(initial_actions, planner, judge, context)
                    results[planner_name][judge_name] = result
                    
                    self.logger.info(f"Completed: {result.total_iterations} iterations, "
                          f"Converged: {result.converged}, "
                          f"Time: {result.execution_time:.2f}s")
                    
                except Exception as e:
                    self.logger.error(f"Error in combination {planner_name} + {judge_name}: {e}")
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