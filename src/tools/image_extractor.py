# pip install -U langchain langchain-openai pydantic python-dotenv loguru
"""
Generating structured data from an image with GPT Vision and LangChain.

This script demonstrates the LCEL (LangChain Expression Language) pattern for
image processing pipelines using RunnableLambda, based on the approach from:
https://medium.com/generative-ai-in-production/generating-structured-data-from-an-image-with-gpt-vision-and-langchain-34aaf3dcb215

Note: TransformChain is deprecated in LangChain 1.x. This script uses RunnableLambda
as the modern replacement for data transformations.
"""
import os
import json
import base64
import sys

import argparse

from typing import Any
from pathlib import Path
from loguru import logger
from langchain_openai import ChatOpenAI
from dotenv import find_dotenv, load_dotenv

from langchain_core.runnables import RunnableLambda, chain

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src import schemas

load_dotenv(find_dotenv())

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "image_extractor.md"
PROMPT = PROMPT_PATH.read_text(encoding="utf-8").strip()

# ─────────────────────────────────────────────────────────────────────────────
# Image Loading Transform using RunnableLambda (replaces deprecated TransformChain)
# ─────────────────────────────────────────────────────────────────────────────
def load_image(inputs: dict[str, Any]) -> dict[str, Any]:
    """Load image from path and encode as base64 data URL.

    This function is wrapped with RunnableLambda to convert a file path
    into a base64-encoded data URL suitable for GPT Vision.
    """
    image_path = inputs["image_path"]

    # Determine MIME type from extension
    ext = os.path.splitext(image_path)[1].lower()
    mime_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".webp": "image/webp",
    }
    mime_type = mime_types.get(ext, "image/jpeg")

    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # Return original inputs plus the new image field
    return {**inputs, "image": f"data:{mime_type};base64,{image_data}"}


# RunnableLambda for image loading - modern LCEL replacement for TransformChain
load_image_chain = RunnableLambda(load_image)


# ─────────────────────────────────────────────────────────────────────────────
# LLM Setup with Structured Output
# ─────────────────────────────────────────────────────────────────────────────
def get_llm(model: str = "gpt-4o-mini") -> ChatOpenAI:
    """Create a ChatOpenAI instance."""
    return ChatOpenAI(
        model=model,
        api_key=OPENAI_API_KEY,
        max_tokens=4096,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Image Analysis Chain using @chain decorator
# ─────────────────────────────────────────────────────────────────────────────
@chain
def image_extraction_chain(inputs: dict[str, Any]) -> schemas.receipt.Receipt:
    """Extract structured data from an image using GPT Vision.

    This chain takes an image (base64 data URL) and extracts receipt information
    into a structured Pydantic model.
    """
    image = inputs["image"]
    model = inputs.get("model", "gpt-4o-mini")

    llm = get_llm(model)
    llm_with_structure = llm.with_structured_output(schemas.receipt.Receipt)

    message = {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": PROMPT,
            },
            {
                "type": "image_url",
                "image_url": {"url": image, "detail": "high"},
            },
        ],
    }

    result = llm_with_structure.invoke([message])
    return result



# ─────────────────────────────────────────────────────────────────────────────
# Full Pipeline: Combines TransformChain with Extraction
# ─────────────────────────────────────────────────────────────────────────────
def extract_receipt_from_image(
    image_path: str,
    model: str = "gpt-4o-mini"
) -> schemas.receipt.Receipt | dict:
    """Full pipeline to extract receipt data from an image file.

    Args:
        image_path: Path to the receipt image file
        model: OpenAI model to use (gpt-4o-mini or gpt-4o)
        use_parser: If True, use JsonOutputParser approach; else use with_structured_output

    Returns:
        Receipt object or dict with extracted data
    """
    # Step 1: Load and encode the image using TransformChain
    logger.info(f"Loading image from: {image_path}")
    image_data = load_image_chain.invoke({"image_path": image_path})

    # Step 2: Extract structured data
    logger.info(f"Extracting receipt data using model: {model}")

    
    result = image_extraction_chain.invoke({
        "image": image_data["image"],
        "model": model,
    })

    return result


# ─────────────────────────────────────────────────────────────────────────────
# Main Entry Point
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Extract structured data from receipt images using GPT Vision and LangChain"
    )
    parser.add_argument(
        "--image-path",
        required=True,
        help="Path to the receipt image file",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        choices=["gpt-4o-mini", "gpt-4o"],
        help="OpenAI model to use (default: gpt-4o-mini)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path for JSON result (optional)",
    )
    args = parser.parse_args()

    # Run extraction
    result = extract_receipt_from_image(
        image_path=args.image_path,
        model=args.model
    )

    # Convert to dict if it's a Pydantic model
    if isinstance(result, schemas.receipt.Receipt):
        result_dict = result.model_dump()
    else:
        result_dict = result

    # Output results
    formatted_json = json.dumps(result_dict, indent=2, ensure_ascii=False)
    logger.info(f"Extracted receipt data:\n{formatted_json}")

    # Optionally save to file
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(formatted_json)
        logger.info(f"Results saved to: {args.output}")
