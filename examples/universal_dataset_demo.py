#!/usr/bin/env python3

"""
Universal Dataset MCP Framework Demo

This example demonstrates how to use the universal dataset framework
to work with multiple embodied AI datasets through a standardized interface.

Key Features Demonstrated:
- Dataset registration and management
- Cross-dataset comparison
- Universal action parsing
- Schema validation
- Cross-domain evaluation setup
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

from shared.dataset_adapters import UniversalDatasetAdapter, TeachDatasetAdapter, ALFReDatasetAdapter

class UniversalDatasetDemo:
    """
    Demonstration class for the universal dataset framework.
    
    Shows how researchers can easily work with multiple datasets
    and compare results across different domains.
    """
    
    def __init__(self):
        self.datasets = {}
        self.setup_datasets()
    
    def setup_datasets(self):
        """Setup and register available datasets."""
        print("🔧 Setting up Universal Dataset Framework")
        print("=" * 60)
        
        # Register TEACh dataset
        teach_path = PROJECT_ROOT / "games"
        if teach_path.exists():
            try:
                self.datasets['teach'] = TeachDatasetAdapter(str(PROJECT_ROOT))
                print("✓ Registered TEACh dataset")
            except Exception as e:
                print(f"⚠ Could not register TEACh dataset: {e}")
        
        # Register ALFReD dataset (uses mock data for demo)
        try:
            # In real usage, this would point to actual ALFReD data
            alfred_path = PROJECT_ROOT / "data" / "alfred"  # Mock path
            self.datasets['alfred'] = ALFReDatasetAdapter(str(alfred_path))
            print("✓ Registered ALFReD dataset (with mock data)")
        except Exception as e:
            print(f"⚠ Could not register ALFReD dataset: {e}")
        
        print(f"\n📊 Total registered datasets: {len(self.datasets)}")
    
    def demonstrate_dataset_schemas(self):
        """Show dataset schemas and capabilities."""
        print("\n" + "=" * 60)
        print("📋 DATASET SCHEMAS AND CAPABILITIES")
        print("=" * 60)
        
        for name, adapter in self.datasets.items():
            print(f"\n🗂️  {name.upper()} Dataset:")
            print(f"   Domain: {adapter.get_domain()}")
            print(f"   Supported splits: {adapter.get_supported_splits()}")
            
            action_space = adapter.get_action_space()
            for agent, actions in action_space.items():
                print(f"   {agent} actions: {', '.join(actions[:5])}{'...' if len(actions) > 5 else ''}")
            
            # Show statistics if data is available
            try:
                stats = adapter.get_statistics()
                print(f"   Episodes: {stats.get('total_episodes', 'N/A')}")
                print(f"   Avg sequence length: {stats.get('avg_sequence_length', 'N/A'):.1f}")
            except Exception as e:
                print(f"   Statistics: {e}")
    
    def demonstrate_episode_loading(self):
        """Show how to load and process episodes from different datasets."""
        print("\n" + "=" * 60)
        print("📥 EPISODE LOADING AND PROCESSING")
        print("=" * 60)
        
        for name, adapter in self.datasets.items():
            print(f"\n🎯 Loading episodes from {name.upper()}:")
            
            try:
                # Sample a few episodes
                episodes = adapter.sample_episodes(n_samples=2, seed=42)
                
                for i, episode in enumerate(episodes[:2]):  # Show first 2
                    print(f"\n   Episode {i+1} ({episode['episode_id']}):")
                    print(f"     Goal: {episode['goal']}")
                    print(f"     Actions: {len(episode['actions'])} steps")
                    print(f"     Domain: {episode['domain']}")
                    
                    # Show first few actions
                    if episode['actions']:
                        print(f"     First actions:")
                        for j, action in enumerate(episode['actions'][:3]):
                            print(f"       {j+1}. {action}")
                        if len(episode['actions']) > 3:
                            print(f"       ... ({len(episode['actions'])-3} more)")
                
            except Exception as e:
                print(f"   Error loading episodes: {e}")
    
    def demonstrate_cross_dataset_comparison(self):
        """Show cross-dataset comparison capabilities."""
        print("\n" + "=" * 60)
        print("🔄 CROSS-DATASET COMPARISON")
        print("=" * 60)
        
        if len(self.datasets) < 2:
            print("⚠ Need at least 2 datasets for comparison")
            return
        
        comparison_data = {}
        
        for name, adapter in self.datasets.items():
            try:
                # Get sample episodes for comparison
                episodes = adapter.sample_episodes(n_samples=5, seed=42)
                
                # Calculate metrics
                action_lengths = [len(ep['actions']) for ep in episodes]
                
                comparison_data[name] = {
                    'domain': adapter.get_domain(),
                    'sample_size': len(episodes),
                    'avg_actions': sum(action_lengths) / len(action_lengths) if action_lengths else 0,
                    'min_actions': min(action_lengths) if action_lengths else 0,
                    'max_actions': max(action_lengths) if action_lengths else 0,
                    'action_space_size': len(list(adapter.get_action_space().values())[0]),
                    'example_goal': episodes[0]['goal'] if episodes else 'N/A'
                }
                
            except Exception as e:
                comparison_data[name] = {'error': str(e)}
        
        # Display comparison
        print("\n📊 Dataset Comparison:")
        print(f"{'Dataset':<12} {'Domain':<18} {'Avg Actions':<12} {'Action Space':<12} {'Example Goal'}")
        print("-" * 80)
        
        for name, data in comparison_data.items():
            if 'error' in data:
                print(f"{name:<12} Error: {data['error']}")
            else:
                goal_preview = data['example_goal'][:30] + "..." if len(data['example_goal']) > 30 else data['example_goal']
                print(f"{name:<12} {data['domain']:<18} {data['avg_actions']:<12.1f} {data['action_space_size']:<12} {goal_preview}")
    
    def demonstrate_universal_format(self):
        """Show the universal format structure."""
        print("\n" + "=" * 60)
        print("🌐 UNIVERSAL FORMAT STRUCTURE")
        print("=" * 60)
        
        if not self.datasets:
            print("⚠ No datasets available")
            return
        
        # Get one example from each dataset
        for name, adapter in self.datasets.items():
            try:
                episodes = adapter.sample_episodes(n_samples=1, seed=42)
                if episodes:
                    episode = episodes[0]
                    
                    print(f"\n📄 {name.upper()} Episode in Universal Format:")
                    universal_fields = {
                        'episode_id': episode.get('episode_id'),
                        'dataset': episode.get('dataset'),
                        'domain': episode.get('domain'),
                        'goal': episode.get('goal', '')[:50] + "..." if len(episode.get('goal', '')) > 50 else episode.get('goal'),
                        'action_count': len(episode.get('actions', [])),
                        'action_space': list(episode.get('action_space', {}).keys()),
                        'metadata_keys': list(episode.get('metadata', {}).keys())
                    }
                    
                    for field, value in universal_fields.items():
                        print(f"   {field}: {value}")
                
            except Exception as e:
                print(f"   Error: {e}")
    
    def demonstrate_research_scenarios(self):
        """Show typical research scenarios enabled by this framework."""
        print("\n" + "=" * 60)
        print("🔬 RESEARCH SCENARIOS ENABLED")
        print("=" * 60)
        
        scenarios = [
            {
                'title': 'Cross-Domain Transfer Learning',
                'description': 'Train planning/judging models on TEACh, evaluate on ALFReD',
                'code': '''
# Train on household tasks
teach_episodes = datasets['teach'].sample_episodes(n_samples=1000)
model = train_planner_judge_model(teach_episodes)

# Evaluate on instruction following
alfred_episodes = datasets['alfred'].sample_episodes(n_samples=100)
transfer_performance = evaluate_model(model, alfred_episodes)
                '''
            },
            {
                'title': 'Multi-Dataset Evaluation Matrix',
                'description': 'Compare all planner-judge combinations across all datasets',
                'code': '''
results = {}
for dataset_name in datasets.keys():
    for planner in ['gpt4', 'deepseek', 'gemini']:
        for judge in ['gpt4', 'deepseek', 'gemini']:
            key = f"{dataset_name}_{planner}_{judge}"
            results[key] = evaluate_combination(dataset_name, planner, judge)
                '''
            },
            {
                'title': 'Action Space Analysis',
                'description': 'Analyze action complexity across different domains',
                'code': '''
action_complexity = {}
for name, adapter in datasets.items():
    episodes = adapter.sample_episodes(n_samples=100)
    complexity = analyze_action_patterns(episodes)
    action_complexity[adapter.get_domain()] = complexity
                '''
            }
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            print(f"\n{i}. {scenario['title']}")
            print(f"   {scenario['description']}")
            print(f"   Example code:")
            for line in scenario['code'].strip().split('\n'):
                print(f"   {line}")
    
    def run_complete_demo(self):
        """Run the complete demonstration."""
        print("🚀 UNIVERSAL DATASET FRAMEWORK DEMONSTRATION")
        print("=" * 80)
        print(f"Project: Task-Agents Multi-Dataset Plan Verification")
        print(f"Framework: MCP-based Universal Dataset Access")
        print("=" * 80)
        
        self.demonstrate_dataset_schemas()
        self.demonstrate_episode_loading()
        self.demonstrate_cross_dataset_comparison()
        self.demonstrate_universal_format()
        self.demonstrate_research_scenarios()
        
        print("\n" + "=" * 80)
        print("✅ DEMONSTRATION COMPLETE")
        print("=" * 80)
        print("\nNext Steps:")
        print("1. Install MCP: pip install mcp")
        print("2. Run MCP server: python mcp-servers/universal-dataset-server.py")
        print("3. Connect your Task-Agents workflow to use MCP tools")
        print("4. Add more dataset adapters for additional domains")
        print("5. Implement cross-dataset evaluation pipelines")

def main():
    """Main demonstration entry point."""
    demo = UniversalDatasetDemo()
    demo.run_complete_demo()

if __name__ == "__main__":
    main()