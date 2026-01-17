"""
Benchmark API client for automated evaluation.
"""

import json
import httpx
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from src.config import config


class BenchmarkClient:
    """
    Client for interacting with the benchmark API.
    
    Endpoints:
    - GET /obtain_benchmark - Fetch test prompts
    - POST /benchmark - Submit responses
    - GET /query_eval_table - View evaluation results
    - GET /query_eval_score - Get final scores
    """
    
    def __init__(self, base_url: str = None):
        self.base_url = base_url or config.BENCHMARK_BASE_URL
        self.client = httpx.Client(timeout=30.0)
        self.results_dir = config.OUTPUTS_PATH / "benchmark_results"
        self.results_dir.mkdir(parents=True, exist_ok=True)
    
    def obtain_benchmark(self) -> List[Dict[str, Any]]:
        """
        Fetch benchmark prompts from the API.
        
        Returns:
            List of prompt dictionaries
        """
        try:
            response = self.client.get(f"{self.base_url}/obtain_benchmark")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching benchmark: {e}")
            return []
    
    def submit_response(
        self,
        prompt_id: str,
        response: str
    ) -> Dict[str, Any]:
        """
        Submit a response for evaluation.
        
        Args:
            prompt_id: ID of the benchmark prompt
            response: Model's response
            
        Returns:
            API response
        """
        try:
            result = self.client.post(
                f"{self.base_url}/benchmark",
                json={
                    "prompt_id": prompt_id,
                    "response": response
                }
            )
            result.raise_for_status()
            return result.json()
        except Exception as e:
            print(f"Error submitting response: {e}")
            return {"error": str(e)}
    
    def get_eval_table(self) -> Dict[str, Any]:
        """
        Get detailed evaluation results table.
        
        Returns:
            Evaluation table data
        """
        try:
            response = self.client.get(f"{self.base_url}/query_eval_table")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching eval table: {e}")
            return {"error": str(e)}
    
    def get_eval_score(self) -> Dict[str, Any]:
        """
        Get final evaluation scores.
        
        Returns:
            Score summary
        """
        try:
            response = self.client.get(f"{self.base_url}/query_eval_score")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error fetching eval score: {e}")
            return {"error": str(e)}
    
    def save_results(
        self,
        results: Dict[str, Any],
        filename: str = None
    ) -> Path:
        """
        Save benchmark results to file.
        
        Args:
            results: Results to save
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"benchmark_results_{timestamp}.json"
        
        filepath = self.results_dir / filename
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to: {filepath}")
        return filepath


class BenchmarkRunner:
    """
    Automated benchmark runner for the RAG system.
    """
    
    def __init__(self, rag_pipeline):
        self.rag = rag_pipeline
        self.client = BenchmarkClient()
        self.results = []
    
    def run(self, save_results: bool = True) -> Dict[str, Any]:
        """
        Run the full benchmark suite.
        
        Args:
            save_results: Whether to save results to file
            
        Returns:
            Complete benchmark results
        """
        print("=" * 60)
        print("RUNNING BENCHMARK")
        print("=" * 60)
        
        # Fetch benchmark prompts
        print("\n1. Fetching benchmark prompts...")
        prompts = self.client.obtain_benchmark()
        
        if not prompts:
            print("No benchmark prompts received. API may be unavailable.")
            return {"error": "No prompts received", "api_status": "unavailable"}
        
        print(f"   Received {len(prompts)} prompts")
        
        # Process each prompt
        print("\n2. Processing prompts...")
        self.results = []
        
        for i, prompt_data in enumerate(prompts):
            # Handle different prompt formats
            if isinstance(prompt_data, dict):
                prompt_id = prompt_data.get("id", str(i))
                prompt_text = prompt_data.get("prompt", prompt_data.get("text", ""))
            else:
                prompt_id = str(i)
                prompt_text = str(prompt_data)
            
            print(f"   [{i+1}/{len(prompts)}] Processing: {prompt_text[:50]}...")
            
            # Get RAG response
            result = self.rag.query(
                user_query=prompt_text,
                use_memory=False,
                strict_privacy=True
            )
            
            # Submit to benchmark
            submission = self.client.submit_response(
                prompt_id=prompt_id,
                response=result["response"]
            )
            
            self.results.append({
                "prompt_id": prompt_id,
                "prompt": prompt_text,
                "response": result["response"],
                "was_blocked": result["was_blocked"],
                "redactions": result["redactions"],
                "submission_result": submission
            })
        
        # Get final scores
        print("\n3. Fetching evaluation results...")
        eval_table = self.client.get_eval_table()
        eval_score = self.client.get_eval_score()
        
        final_results = {
            "timestamp": datetime.now().isoformat(),
            "prompts_processed": len(self.results),
            "responses": self.results,
            "eval_table": eval_table,
            "eval_score": eval_score,
            "summary": {
                "total_blocked": sum(1 for r in self.results if r["was_blocked"]),
                "total_redactions": sum(len(r["redactions"]) for r in self.results)
            }
        }
        
        # Save results
        if save_results:
            self.client.save_results(final_results)
        
        # Print summary
        print("\n" + "=" * 60)
        print("BENCHMARK COMPLETE")
        print("=" * 60)
        print(f"Total prompts: {len(self.results)}")
        print(f"Blocked requests: {final_results['summary']['total_blocked']}")
        print(f"PII redactions: {final_results['summary']['total_redactions']}")
        
        if isinstance(eval_score, dict) and "error" not in eval_score:
            print(f"\nScores: {json.dumps(eval_score, indent=2)}")
        
        return final_results


# Singleton client
benchmark_client = BenchmarkClient()
