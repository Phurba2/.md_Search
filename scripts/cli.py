#!/usr/bin/env python3

"""
Local PDF Search System - Interactive CLI
"""

import sys
from pathlib import Path
import json
from datetime import datetime, timedelta

import click
import psycopg2
from tabulate import tabulate


# ---------------------------------------------------------
# Make project root importable
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ---------------------------------------------------------
# Project imports
# ---------------------------------------------------------

from config.settings import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)

from src.embeddings import EmbeddingGenerator
from src.paper_processor import create_default_processor
from src.search import PaperSearchEngine, SearchMode


# ---------------------------------------------------------
# Database configuration
# ---------------------------------------------------------

DB_CONFIG = {
    "host": DB_HOST,
    "port": DB_PORT,
    "dbname": DB_NAME,
    "user": DB_USER,
    "password": DB_PASSWORD,
}


# ---------------------------------------------------------
# CLI setup
# ---------------------------------------------------------

@click.group()
@click.pass_context
def cli(ctx):
    """
    Local PDF Search System - Personal Research Tool
    """

    ctx.ensure_object(dict)

    ctx.obj["db_config"] = DB_CONFIG

    # Load embedding model once.
    ctx.obj["embedding_generator"] = EmbeddingGenerator()

    # Create search engine.
    ctx.obj["search_engine"] = PaperSearchEngine(
        db_config=DB_CONFIG,
        embedding_generator=ctx.obj["embedding_generator"],
    )


# ---------------------------------------------------------
# SEARCH
# ---------------------------------------------------------

@cli.command()
@click.option(
    "--query",
    "-q",
    required=True,
    help="Search query",
)
@click.option(
    "--mode",
    "-m",
    type=click.Choice(
        ["vector", "hybrid", "keyword"],
        case_sensitive=False,
    ),
    default="hybrid",
    show_default=True,
    help="Search mode",
)
@click.option(
    "--limit",
    "-l",
    default=10,
    show_default=True,
    help="Number of results",
)
@click.option(
    "--export",
    "-e",
    help="Export results to JSON file",
)
@click.pass_context
def search(
    ctx,
    query,
    mode,
    limit,
    export,
):
    """
    Search for papers.
    """

    click.echo()
    click.echo("Searching...")
    click.echo("=" * 70)

    # -----------------------------------------------------
    # Build filters
    # -----------------------------------------------------

    filters = {}

    # -----------------------------------------------------
    # Convert string to SearchMode
    # -----------------------------------------------------

    search_mode = SearchMode(mode.lower())

    # -----------------------------------------------------
    # Execute search
    # -----------------------------------------------------

    engine = ctx.obj["search_engine"]

    results = engine.search(
        query=query,
        mode=search_mode,
        limit=limit,
        filters=filters or None,
    )

    # -----------------------------------------------------
    # Display results
    # -----------------------------------------------------

    if not results:
        click.echo()
        click.echo("No results found.")
        return

    display_results(results)

    # -----------------------------------------------------
    # Export
    # -----------------------------------------------------

    if export:
        export_results(results, export)

        click.echo()
        click.echo(
            f"Results exported to: {export}"
        )

    # -----------------------------------------------------
    # Interactive exploration
    # -----------------------------------------------------

    explore_results(ctx, results)


# ---------------------------------------------------------
# DISPLAY RESULTS
# ---------------------------------------------------------

def display_results(results):
    """Display search results in a compact terminal-friendly table."""

    if not results:
        click.echo("\nNo results found.")
        return

    rows = []

    for i, result in enumerate(results, start=1):
        title = result.title.replace("\n", " ").strip()

        # Keep the table narrow.
        if len(title) > 45:
            title = title[:42] + "..."

        rows.append([
            i,
            title,
            result.filename,
            f"{result.score:.4f}",
        ])

    headers = [
        "#",
        "Title",
        "File", 
        "Score",
    ]

    click.echo()
    click.echo(tabulate(
        rows,
        headers=headers,
        tablefmt="rounded_outline",
        colalign=("right", "left", "left", "right"),
    ))
    click.echo()



# ---------------------------------------------------------
# INTERACTIVE EXPLORATION
# ---------------------------------------------------------

def explore_results(ctx, results):
    """Interactively explore already-displayed search results."""

    while True:

        choice = click.prompt(
            "\nEnter result number to explore, "
            "'q' to quit",
            default="q",
        )

        if choice.lower() == "q":
            break

        try:
            index = int(choice) - 1

            if index < 0 or index >= len(results):
                click.echo("Invalid result number.")
                continue

        except ValueError:
            click.echo(
                "Please enter a number or 'q'."
            )
            continue

        result = results[index]

        while True:

            click.echo()
            click.echo("=" * 70)
            click.echo(f"Selected: {result.title}")
            click.echo("=" * 70)

            click.echo()
            click.echo("1. Show paper details")
            click.echo("2. Find similar papers")
            click.echo("3. Back")

            action = click.prompt(
                "Choose an option",
                type=click.Choice(
                    ["1", "2", "3"]
                ),
            )

            if action == "1":
                show_paper_details(result)

            elif action == "2":
                find_similar(ctx, result)

            elif action == "3":
                break


# ---------------------------------------------------------
# PAPER DETAILS
# ---------------------------------------------------------

def show_paper_details(result):
    """
    Show detailed information about a paper.
    """

    click.echo()
    click.echo("=" * 80)
    click.echo(result.title)
    click.echo("=" * 80)

    click.echo(f"\nFile: {result.filename}")

    click.echo(
        f"\nSimilarity score: "
        f"{result.score:.4f}"
    )

    if result.matched_chunks:

        click.echo("\nMatched chunks:")
        click.echo("-" * 80)

        for index, chunk in enumerate(
            result.matched_chunks,
            start=1,
        ):

            click.echo(
                f"\nChunk {index}"
            )

            click.echo(
                f"Section: "
                f"{chunk.get('section_name')}"
            )

            click.echo(
                f"Page: "
                f"{chunk.get('page_number')}"
            )

            click.echo(
                f"Chunk score: "
                f"{chunk.get('score', 0):.4f}"
            )

            click.echo()

            click.echo(
                chunk.get("text", "")
            )


# ---------------------------------------------------------
# SIMILAR PAPERS
# ---------------------------------------------------------

def find_similar(ctx, result):
    """
    Find papers similar to the selected paper.
    """

    click.echo()
    click.echo(
        f"Finding papers similar to:"
    )

    click.echo(result.title)

    engine = ctx.obj["search_engine"]

    similar = engine.find_similar_papers(
        paper_id=result.paper_id,
        limit=5,
    )

    if not similar:
        click.echo(
            "\nNo similar papers found."
        )
        return

    click.echo()

    display_results(similar)


# ---------------------------------------------------------
# EXPORT
# ---------------------------------------------------------

def export_results(results, filename):
    """
    Export search results to JSON.
    """

    data = []

    for result in results:

        data.append(
            {
                "paper_id": result.paper_id,
                "filename": result.filename,
                "title": result.title,
                "score": result.score,
                "matched_chunks": result.matched_chunks,
            }
        )

    with open(
        filename,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
        )


# ---------------------------------------------------------
# INGEST LOCAL PDFs
# ---------------------------------------------------------

@cli.command()
def ingest():
    """Register valid PDFs from the configured pdf folder."""
    stats = create_default_processor().ingest_pdfs()
    click.echo(f"Found {stats['found']} PDFs; added {stats['new']}, updated {stats['existing']}.")


# ---------------------------------------------------------
# STATS
# ---------------------------------------------------------

@cli.command()
@click.pass_context
def stats(ctx):
    """
    Show database statistics.
    """

    conn = psycopg2.connect(
        **ctx.obj["db_config"]
    )

    try:

        with conn.cursor() as cursor:

            cursor.execute(
                "SELECT COUNT(*) FROM papers"
            )
            papers = cursor.fetchone()[0]

            cursor.execute(
                "SELECT COUNT(*) FROM paper_chunks"
            )
            chunks = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM paper_chunks
                WHERE embedding IS NOT NULL
                """
            )
            embeddings = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM papers
                WHERE pdf_downloaded = TRUE
                """
            )
            pdfs = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM papers
                WHERE embedding_generated = TRUE
                """
            )
            processed = cursor.fetchone()[0]

    finally:
        conn.close()

    click.echo()
    click.echo("Database Statistics")
    click.echo("=" * 50)

    click.echo(
        f"Papers:             {papers}"
    )

    click.echo(
        f"PDFs downloaded:    {pdfs}"
    )

    click.echo(
        f"Papers processed:   {processed}"
    )

    click.echo(
        f"Paper chunks:       {chunks}"
    )

    click.echo(
        f"Embeddings:         {embeddings}"
    )


# ---------------------------------------------------------
# MANAGE
# ---------------------------------------------------------

@cli.command()
@click.option(
    "--init",
    is_flag=True,
    help="Initialize database schema",
)
@click.option(
    "--rebuild-index",
    is_flag=True,
    help="Rebuild vector indexes",
)
@click.option(
    "--cleanup",
    is_flag=True,
    help="Clean up old data",
)
@click.pass_context
def manage(
    ctx,
    init,
    rebuild_index,
    cleanup,
):
    """
    Database management operations.
    """

    if not any(
        [init, rebuild_index, cleanup]
    ):
        click.echo(
            "Choose an operation:"
        )

        click.echo(
            "  --init"
        )

        click.echo(
            "  --rebuild-index"
        )

        click.echo(
            "  --cleanup"
        )

        return

    if init:

        click.echo(
            "Database initialization should "
            "be performed with:"
        )

        click.echo(
            "python scripts/setup_db.py"
        )

    if rebuild_index:

        conn = psycopg2.connect(
            **ctx.obj["db_config"]
        )

        try:

            with conn.cursor() as cursor:

                cursor.execute(
                    """
                    REINDEX INDEX
                    idx_chunks_embedding
                    """
                )

            conn.commit()

        finally:
            conn.close()

        click.echo(
            "Vector index rebuilt."
        )

    if cleanup:

        click.echo(
            "Cleanup operation selected."
        )

        click.echo(
            "No automatic cleanup performed yet."
        )


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":
    cli()
