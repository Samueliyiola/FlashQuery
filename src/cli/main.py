#!/usr/bin/env python3
# src/cli/main.py
"""CLI entry point for flashquery - AI-powered PostgreSQL query optimizer."""

import sys
import click


@click.command(
    help="flashquery: AI-powered PostgreSQL query optimizer - flash fast, query smart."
)
@click.option(
    "--query", "-q",
    type=str,
    help="SQL query string to analyze."
)
@click.option(
    "--file", "-f",
    type=click.Path(exists=True, readable=True, dir_okay=False),
    help="Path to a SQL file containing the target query."
)
@click.option(
    "--use-llm",
    is_flag=True,
    default=False,
    help="Engage LLM reasoning for complex query rewrites."
)
@click.option(
    "--pr",
    is_flag=True,
    default=False,
    help="Automatically open a GitHub PR with the validated index migration."
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=False,
    help="Print detailed execution plan JSON and timing statistics."
)
def main(query: str, file: str, use_llm: bool, pr: bool, verbose: bool):
    """
    Main CLI entry point for flashquery.
    
    Resolves SQL input from one of three sources:
    1. Direct --query string
    2. --file path to .sql file
    3. stdin (piped input)
    """
    
    # STEP 1: RESOLVE SQL INPUT
    target_sql = None
    
    if query:
        # Direct query string provided
        target_sql = query.strip()
        if verbose:
            click.echo(f"Query from --query flag")
    
    elif file:
        # Read from file
        try:
            with open(file, "r", encoding="utf-8") as f:
                target_sql = f.read().strip()
            if verbose:
                click.echo(f"Query from --file: {file}")
        except Exception as e:
            click.secho(f"Error reading file: {e}", fg="red", err=True)
            sys.exit(1)
    
    elif not sys.stdin.isatty():
        # Input was piped in: e.g. cat query.sql | flashquery
        target_sql = sys.stdin.read().strip()
        if verbose:
            click.echo("📥 Query from stdin (piped input)")
    
    # STEP 2: VALIDATE INPUT
    if not target_sql:
        click.secho("Error: No SQL query provided.", fg="red", err=True)
        click.echo("\n Provide a query via -q, -f, or stdin:")
        click.echo('flashquery -q "SELECT * FROM orders WHERE customer_id = 42000"')
        click.echo('flashquery -f ./queries/slow.sql')
        click.echo('cat query.sql | flashquery')
        sys.exit(1)
    
    # STEP 3: VALIDATE FLAG COMBINATIONS
    # --pr doesn't make sense without an optimization
    # For now, we'll just warn. Later this will be handled by the engine.
    if pr and not use_llm:
        click.secho("Warning: --pr without --use-llm will only use rule-based optimizations.", fg="yellow")
        click.echo("For complex rewrites, consider adding --use-llm.\n")
    
    # STEP 4: DISPLAY RUN METADATA
    click.secho("\n flashquery analyzer initializing...", fg="cyan", bold=True)
    
    if verbose:
        click.echo(f"• LLM Mode:   {'Enabled' if use_llm else 'Disabled (Rule-based)'}")
        click.echo(f"• Create PR:  {'Yes' if pr else 'No'}")
        # Show query preview (truncate if too long)
        query_preview = target_sql[:80] + "..." if len(target_sql) > 80 else target_sql
        click.echo(f"• Query:      {query_preview}")
    else:
        click.echo(f"• Query length: {len(target_sql)} characters")
    
    click.echo()
    
    # STEP 5: CALL THE ENGINE (COMING NEXT)
    click.secho("✓ Target query loaded successfully.", fg="green")
    click.echo("🔄 Connecting to PostgreSQL engine...")
    
    # TODO: In the next phase, we'll call:
    # from src.core.pipeline import run_optimization
    # result = run_optimization(
    #     sql=target_sql,
    #     use_llm=use_llm,
    #     create_pr=pr,
    #     verbose=verbose
    # )
    # 
    # if result.success:
    #     click.secho(f"\n✅ Optimization complete!", fg="green")
    #     click.echo(f"   Before: {result.before_ms}ms → After: {result.after_ms}ms")
    #     click.echo(f"   Improvement: {result.improvement_pct}%")
    #     if result.pr_url:
    #         click.echo(f"   PR: {result.pr_url}")
    #     sys.exit(0)
    # else:
    #     click.secho(f"\n❌ Optimization failed: {result.error}", fg="red", err=True)
    #     sys.exit(1)
    
    click.echo("\n📝 This is a placeholder. The core engine is coming next!")
    click.echo("   Coming soon: Database connection → EXPLAIN analysis → Optimization")
    
    sys.exit(0)


if __name__ == "__main__":
    main()