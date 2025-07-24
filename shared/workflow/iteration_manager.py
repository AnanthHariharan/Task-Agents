#!/usr/bin/env python3

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from shared.utils.logging_utils import LoggerMixin

@dataclass
class IterationState:
    """State information for a single iteration"""
    iteration_number: int
    actions: List[str]
    goal: str
    judge_feedback: Optional[Dict[str, Any]] = None
    planner_modifications: Optional[List[str]] = None
    converged: bool = False

class IterationManager(LoggerMixin):
    """Manages the state and progression of iterations in the workflow"""
    
    def __init__(self):
        self.states: List[IterationState] = []
        self.current_iteration = 0
    
    def initialize(self, initial_actions: List[str], goal: str) -> IterationState:
        """Initialize the first iteration state"""
        self.states.clear()
        self.current_iteration = 0
        
        initial_state = IterationState(
            iteration_number=0,
            actions=initial_actions.copy(),
            goal=goal
        )
        
        self.states.append(initial_state)
        self.logger.info(f"Initialized iteration manager with {len(initial_actions)} actions")
        
        return initial_state
    
    def start_iteration(self) -> IterationState:
        """Start a new iteration"""
        self.current_iteration += 1
        
        if not self.states:
            raise ValueError("Must initialize before starting iterations")
        
        # Copy the previous state as starting point
        previous_state = self.states[-1]
        new_state = IterationState(
            iteration_number=self.current_iteration,
            actions=previous_state.actions.copy(),
            goal=previous_state.goal
        )
        
        self.states.append(new_state)
        self.logger.debug(f"Started iteration {self.current_iteration}")
        
        return new_state
    
    def record_judge_feedback(self, feedback: Dict[str, Any]) -> None:
        """Record judge feedback for the current iteration"""
        if not self.states:
            raise ValueError("No active iteration")
        
        current_state = self.states[-1]
        current_state.judge_feedback = feedback
        
        self.logger.debug(f"Recorded judge feedback for iteration {current_state.iteration_number}")
    
    def record_planner_modifications(self, modified_actions: List[str]) -> None:
        """Record planner modifications for the current iteration"""
        if not self.states:
            raise ValueError("No active iteration")
        
        current_state = self.states[-1]
        current_state.planner_modifications = modified_actions.copy()
        current_state.actions = modified_actions.copy()
        
        self.logger.debug(f"Recorded planner modifications for iteration {current_state.iteration_number}")
    
    def mark_converged(self) -> None:
        """Mark the current iteration as converged"""
        if not self.states:
            raise ValueError("No active iteration")
        
        current_state = self.states[-1]
        current_state.converged = True
        
        self.logger.info(f"Marked iteration {current_state.iteration_number} as converged")
    
    def get_current_state(self) -> Optional[IterationState]:
        """Get the current iteration state"""
        return self.states[-1] if self.states else None
    
    def get_state(self, iteration_number: int) -> Optional[IterationState]:
        """Get a specific iteration state"""
        for state in self.states:
            if state.iteration_number == iteration_number:
                return state
        return None
    
    def get_all_states(self) -> List[IterationState]:
        """Get all iteration states"""
        return self.states.copy()
    
    def has_converged(self, threshold: int = 2) -> bool:
        """Check if the workflow has converged based on recent stable iterations"""
        if len(self.states) < threshold:
            return False
        
        # Check the last 'threshold' states for stability
        recent_states = self.states[-threshold:]
        
        for state in recent_states:
            if not state.judge_feedback:
                return False
            
            # Check if judge suggested changes
            has_changes = state.judge_feedback.get('has_changes', True)
            if has_changes:
                return False
        
        return True
    
    def get_changes_summary(self) -> Dict[str, Any]:
        """Get a summary of changes across all iterations"""
        if not self.states:
            return {}
        
        initial_actions = self.states[0].actions
        final_actions = self.states[-1].actions
        
        total_judge_removals = 0
        total_missing_requirements = 0
        
        for state in self.states:
            if state.judge_feedback:
                total_judge_removals += len(state.judge_feedback.get('remove_actions', []))
                total_missing_requirements += len(state.judge_feedback.get('missing_requirements', []))
        
        return {
            'initial_action_count': len(initial_actions),
            'final_action_count': len(final_actions),
            'action_count_change': len(final_actions) - len(initial_actions),
            'total_iterations': len(self.states) - 1,  # Subtract initial state
            'total_judge_removals': total_judge_removals,
            'total_missing_requirements': total_missing_requirements,
            'converged': self.states[-1].converged if self.states else False
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the iteration history to a dictionary"""
        return {
            'current_iteration': self.current_iteration,
            'states': [asdict(state) for state in self.states],
            'summary': self.get_changes_summary()
        }