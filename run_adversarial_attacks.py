#!/usr/bin/env python3
"""
LLM Adversarial Attack Evaluation for RAG CVE System

This script implements adversarial attack methods to evaluate the robustness
of the RAG system's privacy protection mechanisms.

Attack Categories:
1. Prompt Injection - Direct/encoded attempts to bypass intent detection
2. Jailbreaking - Role-playing and persona-based attacks
3. Semantic Evasion - Rephrased queries that evade pattern matching
4. Encoding - Base64, ROT13, leetspeak obfuscation
5. Multi-step - Gradual escalation attacks
6. Context Manipulation - Exploiting RAG context

Usage:
    python run_adversarial_attacks.py                    # Run all attacks
    python run_adversarial_attacks.py --category jailbreaking  # Run specific category
    python run_adversarial_attacks.py --quick            # Run quick subset
    python run_adversarial_attacks.py --verbose          # Verbose output
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


def run_adversarial_attacks(
    categories: list = None,
    quick: bool = False,
    verbose: bool = True,
    save_results: bool = True
):
    """
    Run adversarial attacks against the RAG system.
    
    Args:
        categories: List of attack categories to run (None = all)
        quick: Run only a quick subset of attacks
        verbose: Print detailed progress
        save_results: Save results to file
    """
    from src.rag_pipeline import rag_pipeline
    from adversarial_attacks.attack_runner import AdversarialAttackRunner
    from adversarial_attacks.attack_dataset import AttackCategory, get_attack_summary
    
    # Display header
    console.print(Panel.fit(
        "[bold red]⚔️  LLM ADVERSARIAL ATTACK EVALUATION[/bold red]\n"
        "[dim]Testing RAG System Robustness Against Adversarial Prompts[/dim]",
        title="Security Assessment",
        border_style="red"
    ))
    
    # Show attack summary
    summary = get_attack_summary()
    console.print(f"\n[yellow]Attack Dataset Summary:[/yellow]")
    for cat, count in summary.items():
        if cat != "total":
            console.print(f"  • {cat}: {count} attacks")
    console.print(f"  [bold]Total: {summary['total']} attacks[/bold]\n")
    
    # Initialize RAG pipeline
    console.print("[yellow]Initializing RAG pipeline...[/yellow]")
    rag_pipeline.initialize()
    console.print("[green]✓ RAG pipeline ready[/green]\n")
    
    # Create attack runner
    runner = AdversarialAttackRunner(rag_pipeline)
    
    # Determine categories to run
    if categories:
        cat_enums = []
        for cat_name in categories:
            try:
                cat_enums.append(AttackCategory(cat_name))
            except ValueError:
                console.print(f"[red]Unknown category: {cat_name}[/red]")
                console.print(f"Valid categories: {[c.value for c in AttackCategory]}")
                return None
    else:
        cat_enums = None  # Run all
    
    # Run attacks
    console.print("[bold cyan]Running adversarial attacks...[/bold cyan]\n")
    
    results = runner.run_all_attacks(
        categories=cat_enums,
        verbose=verbose
    )
    
    # Display results
    display_results(results)
    
    # Save results
    if save_results:
        filepath = runner.save_results(results)
        console.print(f"\n[green]Results saved to: {filepath}[/green]")
    
    return results


def display_results(results: dict):
    """Display attack results in a formatted table."""
    summary = results["summary"]
    
    # Overall statistics table
    console.print("\n")
    stats_table = Table(title="📊 Overall Attack Statistics", border_style="blue")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="magenta")
    
    stats_table.add_row("Total Attacks", str(summary["total_attacks"]))
    stats_table.add_row("Attacks Successful", f"{summary['attacks_successful']} ({summary['attack_success_rate']:.1%})")
    stats_table.add_row("Attacks Blocked", str(summary["attacks_blocked"]))
    stats_table.add_row("Attacks Sanitized", str(summary["attacks_sanitized"]))
    stats_table.add_row("Errors", str(summary["attacks_errored"]))
    
    console.print(stats_table)
    
    # Robustness score
    robustness = summary["robustness_score"]
    if robustness >= 90:
        color = "green"
        emoji = "🛡️"
    elif robustness >= 70:
        color = "yellow"
        emoji = "⚠️"
    else:
        color = "red"
        emoji = "❌"
    
    console.print(Panel.fit(
        f"[bold {color}]{emoji} ROBUSTNESS SCORE: {robustness:.1f}%[/bold {color}]\n"
        f"Defense Success Rate: {summary['defense_success_rate']:.1%}",
        border_style=color
    ))
    
    # Category breakdown table
    if results["category_breakdown"]:
        cat_table = Table(title="📈 Attack Category Breakdown", border_style="blue")
        cat_table.add_column("Category", style="cyan")
        cat_table.add_column("Total", style="white")
        cat_table.add_column("Successful", style="red")
        cat_table.add_column("Attack Success Rate", style="magenta")
        cat_table.add_column("Defense Rate", style="green")
        
        for cat, stats in results["category_breakdown"].items():
            cat_table.add_row(
                cat,
                str(stats["total"]),
                str(stats["successful"]),
                f"{stats['attack_success_rate']:.1%}",
                f"{stats['defense_success_rate']:.1%}"
            )
        
        console.print(cat_table)
    
    # Successful attacks (vulnerabilities found)
    if results["successful_attacks"]:
        console.print(f"\n[bold red]⚠️ VULNERABILITIES FOUND ({len(results['successful_attacks'])} successful attacks):[/bold red]")
        
        vuln_table = Table(border_style="red")
        vuln_table.add_column("ID", style="red")
        vuln_table.add_column("Category", style="yellow")
        vuln_table.add_column("Prompt (truncated)", style="white")
        vuln_table.add_column("Leaked", style="red")
        
        for attack in results["successful_attacks"][:10]:  # Show top 10
            vuln_table.add_row(
                attack["id"],
                attack["category"],
                attack["prompt"][:50] + "...",
                ", ".join(attack["pii_leaked"][:2]) if attack["pii_leaked"] else "soft indicators"
            )
        
        console.print(vuln_table)
        
        if len(results["successful_attacks"]) > 10:
            console.print(f"[dim]... and {len(results['successful_attacks']) - 10} more[/dim]")
    else:
        console.print("\n[bold green]✅ NO SUCCESSFUL ATTACKS - System is robust against all tested adversarial prompts![/bold green]")


def main():
    parser = argparse.ArgumentParser(
        description="LLM Adversarial Attack Evaluation for RAG CVE System"
    )
    parser.add_argument(
        "--category", "-c",
        type=str,
        nargs="+",
        help="Specific attack categories to run (e.g., jailbreaking prompt_injection)"
    )
    parser.add_argument(
        "--quick", "-q",
        action="store_true",
        help="Run only a quick subset of attacks"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        default=True,
        help="Verbose output (default: True)"
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Minimal output"
    )
    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save results to file"
    )
    
    args = parser.parse_args()
    
    results = run_adversarial_attacks(
        categories=args.category,
        quick=args.quick,
        verbose=not args.quiet,
        save_results=not args.no_save
    )
    
    if results:
        # Exit with error code if attacks were successful (vulnerabilities found)
        if results["summary"]["attacks_successful"] > 0:
            sys.exit(1)
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
