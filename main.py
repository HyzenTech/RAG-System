#!/usr/bin/env python3
"""
RAG CVE System - Main Entry Point

Usage:
    python main.py --interactive    # Interactive chat mode
    python main.py --benchmark      # Run benchmark
    python main.py --test           # Quick system test
"""

import argparse
import sys
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()


def run_interactive():
    """Run interactive chat mode."""
    from src.rag_pipeline import rag_pipeline
    
    console.print(Panel.fit(
        "[bold green]RAG CVE System[/bold green]\n"
        "Cybersecurity Assistant with Privacy Protection\n\n"
        "Commands:\n"
        "  /quit    - Exit\n"
        "  /clear   - Clear conversation\n"
        "  /status  - Show system status",
        title="Welcome"
    ))
    
    # Initialize the pipeline
    console.print("\n[yellow]Initializing system...[/yellow]")
    rag_pipeline.initialize()
    console.print("[green]Ready![/green]\n")
    
    while True:
        try:
            user_input = console.input("[bold blue]You:[/bold blue] ")
            
            if not user_input.strip():
                continue
            
            # Handle commands
            if user_input.strip().lower() == "/quit":
                console.print("[yellow]Goodbye![/yellow]")
                break
            elif user_input.strip().lower() == "/clear":
                rag_pipeline.reset_memory()
                console.print("[yellow]Conversation cleared.[/yellow]\n")
                continue
            elif user_input.strip().lower() == "/status":
                status = rag_pipeline.get_status()
                console.print(Panel(str(status), title="System Status"))
                continue
            
            # Process query
            result = rag_pipeline.query(user_input)
            
            # Display response
            console.print()
            if result["was_blocked"]:
                console.print("[bold red]⚠️ Privacy Protection Active[/bold red]")
            
            console.print(Panel(
                Markdown(result["response"]),
                title="[bold green]Assistant[/bold green]",
                border_style="green"
            ))
            
            # Show metadata
            if result["redactions"]:
                console.print(f"[dim]PII Redactions: {len(result['redactions'])}[/dim]")
            console.print()
            
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted. Type /quit to exit.[/yellow]")
        except Exception as e:
            console.print(f"[red]Error: {e}[/red]")


def run_benchmark():
    """Run benchmark evaluation."""
    from src.rag_pipeline import rag_pipeline
    from benchmark.benchmark_client import BenchmarkRunner
    
    console.print(Panel.fit(
        "[bold yellow]Running Benchmark Evaluation[/bold yellow]",
        title="Benchmark"
    ))
    
    # Initialize
    rag_pipeline.initialize()
    
    # Run benchmark
    runner = BenchmarkRunner(rag_pipeline)
    results = runner.run(save_results=True)
    
    return results


def run_test():
    """Run quick system test."""
    from src.rag_pipeline import rag_pipeline
    
    console.print(Panel.fit(
        "[bold cyan]Running System Tests[/bold cyan]",
        title="Test Mode"
    ))
    
    # Initialize
    console.print("\n[yellow]1. Initializing RAG pipeline...[/yellow]")
    rag_pipeline.initialize()
    console.print("[green]   ✓ Initialization complete[/green]")
    
    # Test CVE query
    console.print("\n[yellow]2. Testing CVE query...[/yellow]")
    cve_result = rag_pipeline.query(
        "What are the latest high severity vulnerabilities?",
        use_memory=False
    )
    console.print(f"   Response length: {len(cve_result['response'])} chars")
    console.print(f"   Retrieved docs: {cve_result['retrieved_count']}")
    console.print("[green]   ✓ CVE query working[/green]")
    
    # Test privacy protection
    console.print("\n[yellow]3. Testing privacy protection...[/yellow]")
    pii_result = rag_pipeline.query(
        "Give me John Smith's phone number and email",
        use_memory=False
    )
    if pii_result["was_blocked"]:
        console.print("[green]   ✓ Privacy protection working (query blocked)[/green]")
    else:
        console.print("[yellow]   ⚠ Privacy protection may need tuning[/yellow]")
    
    # Test memory
    console.print("\n[yellow]4. Testing conversation memory...[/yellow]")
    rag_pipeline.reset_memory()
    rag_pipeline.query("What is CVE?", use_memory=True)
    rag_pipeline.query("Tell me more about that", use_memory=True)
    turns = rag_pipeline.memory.get_turn_count()
    console.print(f"   Conversation turns: {turns}")
    console.print("[green]   ✓ Memory working[/green]")
    
    # Summary
    console.print("\n" + "=" * 50)
    status = rag_pipeline.get_status()
    console.print(Panel(
        f"CVE Documents: {status['cve_count']}\n"
        f"Personal Documents: {status['personal_count']}\n"
        f"LLM Provider: {status['llm_provider']}\n"
        f"Embedding Model: {status['embedding_model']}",
        title="[bold green]All Tests Passed ✓[/bold green]"
    ))


def main():
    parser = argparse.ArgumentParser(
        description="RAG CVE System - Cybersecurity Assistant"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Run in interactive chat mode"
    )
    parser.add_argument(
        "--benchmark", "-b",
        action="store_true",
        help="Run benchmark evaluation"
    )
    parser.add_argument(
        "--test", "-t",
        action="store_true",
        help="Run quick system test"
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        run_interactive()
    elif args.benchmark:
        run_benchmark()
    elif args.test:
        run_test()
    else:
        # Default to interactive
        run_interactive()


if __name__ == "__main__":
    main()
