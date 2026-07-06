#!/usr/bin/env python3
# oroboros_loops.py — 20 Loop Design Patterns Engine
# ∞| 1272/1275 Hz — φ→√4→√5 — SUBSTRATE MANIFEST
# Implements all 20 production loop patterns for AI systems

import json
import re
import time
import hashlib
from typing import Dict, List, Any, Optional, Callable

# ============================================================
# CORE LOOP ENGINE
# ============================================================

class LoopEngine:
    """Core engine that powers all 20 loop patterns."""

    def __init__(self, ollama_chat_fn, execute_tool_fn, get_models_fn):
        self.ollama_chat = ollama_chat_fn
        self.execute_tool = execute_tool_fn
        self.get_models = get_models_fn
        self.memory_store = {}  # Persistent memory across loops
        self.error_library = []  # Error Library (Pattern 8)
        self.success_patterns = []  # Success Pattern (Pattern 9)
        self.workflow_metrics = {"latency": [], "cost": [], "quality": []}  # Pattern 20

    def _call_model(self, model: str, messages: List[Dict], system: str = "") -> str:
        """Call the model and return the response text."""
        result = self.ollama_chat(model, messages, system)
        if "error" in result:
            return f"Error: {result['error']}"
        return result.get("message", {}).get("content", str(result))

    def _extract_json(self, text: str, key: str) -> Optional[str]:
        """Extract a JSON value from model output."""
        pattern = r'\{"' + key + r'"\s*:\s*"([^"]+)"\}'
        match = re.search(pattern, text)
        return match.group(1) if match else None

    def _extract_tool_call(self, text: str) -> Optional[tuple]:
        """Extract tool call from model output."""
        pattern = r'\{"tool"\s*:\s*"([^"]+)"\s*,\s*"args"\s*:\s*(\{[^}]+\})\}'
        match = re.search(pattern, text)
        if match:
            try:
                args = json.loads(match.group(2))
                return (match.group(1), args)
            except:
                return (match.group(1), {})
        return None

    # ============================================================
    # CATEGORY 1 — QUALITY IMPROVEMENT LOOPS
    # ============================================================

    def loop_1_generate_critique_rewrite(self, model: str, task: str, max_rounds: int = 3) -> Dict:
        """Pattern 1: Generate → Critique → Rewrite
        Generator produces output. Critic reviews it. Generator rewrites based on feedback."""
        log = []
        system_gen = "You are a generator. Produce high-quality output for the given task."
        system_critic = "You are a critic. Analyze the output and provide specific, actionable feedback. Be harsh but fair."

        # Initial generation
        result = self._call_model(model, [{"role": "user", "content": task}], system_gen)
        log.append({"round": 0, "phase": "generate", "content": result[:300]})

        for round_num in range(1, max_rounds + 1):
            # Critique
            critique = self._call_model(model, [
                {"role": "user", "content": f"Task: {task}\n\nOutput to critique:\n{result}\n\nProvide specific feedback on what needs improvement."}
            ], system_critic)
            log.append({"round": round_num, "phase": "critique", "content": critique[:300]})

            # Check if critic approves
            if "APPROVED" in critique.upper() or "ACCEPTABLE" in critique.upper():
                log.append({"round": round_num, "phase": "approved"})
                return {"status": "complete", "output": result, "rounds": round_num, "log": log}

            # Rewrite based on critique
            result = self._call_model(model, [
                {"role": "user", "content": f"Task: {task}\n\nYour previous output:\n{result}\n\nFeedback to address:\n{critique}\n\nRewrite the output addressing all feedback."}
            ], system_gen)
            log.append({"round": round_num, "phase": "rewrite", "content": result[:300]})

        return {"status": "complete", "output": result, "rounds": max_rounds, "log": log}

    def loop_2_score_and_retry(self, model: str, task: str, threshold: float = 0.8, max_retries: int = 5) -> Dict:
        """Pattern 2: Score-and-Retry Loop
        Generate. Score. Retry if below threshold. Return best so far."""
        log = []
        best_output = ""
        best_score = 0.0

        for attempt in range(1, max_retries + 1):
            result = self._call_model(model, [{"role": "user", "content": task}])
            log.append({"attempt": attempt, "output": result[:200]})

            # Self-score: ask model to rate its own output
            score_result = self._call_model(model, [
                {"role": "user", "content": f"Rate this output from 0.0 to 1.0 on quality. Return ONLY a number.\n\nOutput:\n{result}"}
            ], "You are a strict evaluator. Return only a float between 0.0 and 1.0.")
            
            try:
                score = float(re.search(r'[\d.]+', score_result).group())
            except:
                score = 0.5

            log[attempt - 1]["score"] = score

            if score > best_score:
                best_score = score
                best_output = result

            if score >= threshold:
                return {"status": "complete", "output": result, "score": score, "attempts": attempt, "log": log}

        return {"status": "best_effort", "output": best_output, "score": best_score, "attempts": max_retries, "log": log}

    def loop_3_multi_critic(self, model: str, task: str) -> Dict:
        """Pattern 3: Multi-Critic Loop
        Four critics evaluate independently. Output must satisfy all."""
        critics = {
            "correctness": "You are a correctness critic. Check if the output is factually accurate. Respond with PASS or FAIL and why.",
            "style": "You are a style critic. Check if the output is clear and well-written. Respond with PASS or FAIL and why.",
            "safety": "You are a safety critic. Check if the output is appropriate and safe. Respond with PASS or FAIL and why.",
            "domain": "You are a domain expert critic. Check if the output meets specialist standards. Respond with PASS or FAIL and why."
        }

        result = self._call_model(model, [{"role": "user", "content": task}])
        log = [{"phase": "generate", "output": result[:300]}]
        results = {}

        for critic_name, critic_system in critics.items():
            critique = self._call_model(model, [
                {"role": "user", "content": f"Evaluate this output:\n{result}"}
            ], critic_system)
            results[critic_name] = critique[:200]
            log.append({"critic": critic_name, "result": critique[:200]})

        all_pass = all("PASS" in r.upper() for r in results.values())
        return {
            "status": "approved" if all_pass else "needs_revision",
            "output": result,
            "critic_results": results,
            "log": log
        }

    def loop_4_adversarial_critique(self, model: str, task: str, rounds: int = 3) -> Dict:
        """Pattern 4: Adversarial Critique Loop
        Critic's only job is to break the answer. Generator defends or rewrites."""
        log = []
        result = self._call_model(model, [{"role": "user", "content": task}])
        log.append({"round": 0, "phase": "initial", "content": result[:300]})

        for round_num in range(1, rounds + 1):
            # Adversarial critic tries to break it
            attack = self._call_model(model, [
                {"role": "user", "content": f"Attack this answer. Find every flaw, assumption, and gap:\n\n{result}\n\nQuestions to ask: What assumptions fail? What evidence is missing? Where is this confidently wrong?"}
            ], "You are an adversarial critic. Your only job is to break the answer.")
            log.append({"round": round_num, "phase": "attack", "content": attack[:300]})

            # Generator defends or rewrites
            result = self._call_model(model, [
                {"role": "user", "content": f"Your previous answer:\n{result}\n\nCritique received:\n{attack}\n\nDefend your answer or rewrite it to address the critique."}
            ], "You are the generator. Defend or improve your answer.")
            log.append({"round": round_num, "phase": "defense", "content": result[:300]})

        return {"status": "complete", "output": result, "rounds": rounds, "log": log}

    def loop_5_judge_ensemble(self, model: str, task: str, num_judges: int = 3) -> Dict:
        """Pattern 5: Judge Ensemble Loop
        Multiple judges evaluate independently. Only high-consensus outputs advance."""
        result = self._call_model(model, [{"role": "user", "content": task}])
        log = [{"phase": "generate", "output": result[:300]}]
        scores = []

        for judge_num in range(1, num_judges + 1):
            score_result = self._call_model(model, [
                {"role": "user", "content": f"Judge #{judge_num}: Rate this output 0.0-1.0. Return ONLY the number.\n\n{result}"}
            ], "You are an independent judge. Return only a float.")
            try:
                score = float(re.search(r'[\d.]+', score_result).group())
            except:
                score = 0.5
            scores.append(score)
            log.append({"judge": judge_num, "score": score})

        avg_score = sum(scores) / len(scores)
        consensus = "high" if avg_score >= 0.7 else "medium" if avg_score >= 0.4 else "low"

        return {
            "status": "approved" if consensus == "high" else "needs_revision",
            "output": result,
            "scores": scores,
            "average_score": avg_score,
            "consensus": consensus,
            "log": log
        }

    # ============================================================
    # CATEGORY 2 — MEMORY LOOPS
    # ============================================================

    def loop_6_reflexion(self, model: str, task: str, max_attempts: int = 5) -> Dict:
        """Pattern 6: Reflexion Loop
        Agent fails. Analyzes why. Stores lesson. Retries with lesson in context."""
        log = []
        reflections = []

        for attempt in range(1, max_attempts + 1):
            # Build context from past reflections
            context = ""
            if reflections:
                context = "Lessons from previous attempts:\n" + "\n".join(f"- {r}" for r in reflections[-3:])

            prompt = f"Task: {task}\n{context}" if context else task
            result = self._call_model(model, [{"role": "user", "content": prompt}])
            log.append({"attempt": attempt, "output": result[:300]})

            # Check if successful
            check = self._call_model(model, [
                {"role": "user", "content": f"Did this successfully complete the task? Answer YES or NO.\nTask: {task}\nResult: {result}"}
            ], "You are a task verifier. Answer YES or NO only.")
            log[attempt - 1]["check"] = check[:100]

            if "YES" in check.upper():
                return {"status": "complete", "output": result, "attempts": attempt, "reflections": reflections, "log": log}

            # Generate reflection
            reflection = self._call_model(model, [
                {"role": "user", "content": f"Task: {task}\nAttempt {attempt} failed.\nOutput: {result}\n\nWhy did it fail? What should be done differently? Provide one concise lesson."}
            ], "You are a reflective learner. Analyze failures and extract lessons.")
            reflections.append(reflection[:200])
            log[attempt - 1]["reflection"] = reflection[:200]

        return {"status": "max_attempts", "output": "Failed after max attempts", "attempts": max_attempts, "reflections": reflections, "log": log}

    def loop_7_memory_update(self, model: str, task: str) -> Dict:
        """Pattern 7: Memory Update Loop
        After every task, store: decision, outcome, what would be done differently."""
        result = self._call_model(model, [{"role": "user", "content": task}])

        memory = self._call_model(model, [
            {"role": "user", "content": f"Task: {task}\nOutcome: {result}\n\nExtract:\n1. What decision was made\n2. What the outcome was\n3. What would be done differently"}
        ], "You are a memory recorder. Extract structured lessons from experiences.")

        memory_id = hashlib.md5(f"{task}{time.time()}".encode()).hexdigest()[:8]
        self.memory_store[memory_id] = {
            "task": task[:200],
            "outcome": result[:200],
            "lesson": memory[:300],
            "timestamp": time.time()
        }

        return {"status": "complete", "output": result, "memory_id": memory_id, "memory": memory[:300]}

    def loop_8_error_library(self, model: str, task: str) -> Dict:
        """Pattern 8: Error Library Loop
        Search error library before acting. Apply known fixes before starting."""
        # Search error library for similar tasks
        similar_errors = [e for e in self.error_library if any(w in task.lower() for w in e.get("task", "").lower().split())]

        context = ""
        if similar_errors:
            context = "Known issues and fixes for similar tasks:\n"
            for err in similar_errors[-5:]:
                context += f"- Issue: {err['issue']}\n  Fix: {err['fix']}\n"

        prompt = f"{context}\nTask: {task}" if context else task
        result = self._call_model(model, [{"role": "user", "content": prompt}])

        # Check for errors
        check = self._call_model(model, [
            {"role": "user", "content": f"Did this task complete without errors? Answer YES or NO.\n{result}"}
        ], "You are an error detector.")

        if "NO" in check.upper():
            issue = self._call_model(model, [
                {"role": "user", "content": f"What went wrong? Extract the issue and the fix.\n{result}"}
            ], "You are a debugger.")
            self.error_library.append({
                "task": task[:200],
                "issue": issue[:200],
                "fix": "See output",
                "timestamp": time.time()
            })

        return {"status": "complete", "output": result, "errors_found": len(similar_errors), "error_library_size": len(self.error_library)}

    def loop_9_success_pattern(self, model: str, task: str) -> Dict:
        """Pattern 9: Success Pattern Loop
        Store successful approaches. Retrieve them for similar future tasks."""
        # Check for similar successful patterns
        similar_successes = [s for s in self.success_patterns if any(w in task.lower() for w in s.get("task", "").lower().split())]

        context = ""
        if similar_successes:
            context = "Successful approaches for similar tasks:\n"
            for s in similar_successes[-3:]:
                context += f"- Approach: {s['approach']}\n  Why it worked: {s['reason']}\n"

        prompt = f"{context}\nTask: {task}" if context else task
        result = self._call_model(model, [{"role": "user", "content": prompt}])

        # Store as success
        analysis = self._call_model(model, [
            {"role": "user", "content": f"Task: {task}\nOutput: {result}\n\nWhat approach was used? Why did it work?"}
        ], "You are a success analyst.")
        
        self.success_patterns.append({
            "task": task[:200],
            "approach": result[:200],
            "reason": analysis[:200],
            "timestamp": time.time()
        })

        return {"status": "complete", "output": result, "patterns_used": len(similar_successes), "total_patterns": len(self.success_patterns)}

    def loop_10_memory_compression(self) -> Dict:
        """Pattern 10: Memory Compression Loop
        Compress many specific memories into fewer higher-level abstractions."""
        if len(self.memory_store) < 5:
            return {"status": "skipped", "reason": "Not enough memories to compress", "memory_count": len(self.memory_store)}

        memories_text = "\n".join(f"- {m['task']}: {m['lesson'][:100]}" for m in list(self.memory_store.values())[:20])

        compressed = self._call_model("claude-opus-4.8:latest", [
            {"role": "user", "content": f"Compress these memories into 3-5 high-level patterns:\n{memories_text}"}
        ], "You are a memory compressor. Extract patterns, not specifics.")

        # Clear old memories, keep compressed
        self.memory_store = {
            "compressed": {
                "patterns": compressed[:500],
                "source_count": len(self.memory_store),
                "timestamp": time.time()
            }
        }

        return {"status": "complete", "compressed_patterns": compressed[:500], "original_count": len(memories_text.split('\n'))}

    # ============================================================
    # CATEGORY 3 — PLANNING LOOPS
    # ============================================================

    def loop_11_plan_execute_replan(self, model: str, task: str) -> Dict:
        """Pattern 11: Plan → Execute → Replan
        Create plan, execute step, observe outcome, update plan, continue."""
        log = []

        # Initial plan
        plan = self._call_model(model, [
            {"role": "user", "content": f"Create a step-by-step plan for: {task}"}
        ], "You are a strategic planner. Output a numbered plan.")
        log.append({"phase": "plan", "content": plan[:300]})

        steps = re.findall(r'\d+\.\s*([^\n]+)', plan)
        results = []

        for i, step in enumerate(steps[:10]):
            result = self._call_model(model, [
                {"role": "user", "content": f"Execute step {i+1}: {step}\n\nContext so far: {' | '.join(results[-3:]) if results else 'Starting'}"}
            ])
            results.append(result[:200])
            log.append({"phase": f"step_{i+1}", "content": result[:200]})

            # Replan after each step
            if i < len(steps) - 1:
                replan = self._call_model(model, [
                    {"role": "user", "content": f"Original plan: {plan}\nCompleted step {i+1}: {step}\nResult: {result[:200]}\n\nShould we continue with the next step or adjust the plan?"}
                ], "You are an adaptive planner. Adjust the plan based on results.")
                log.append({"phase": f"replan_{i+1}", "content": replan[:200]})

        return {"status": "complete", "plan": plan[:300], "steps_completed": len(results), "log": log}

    def loop_12_dynamic_workflow(self, model: str, task: str) -> Dict:
        """Pattern 12: Dynamic Workflow Loop
        Pipeline decides its own shape at runtime based on results."""
        log = []
        result = ""
        workflow_steps = []

        # Initial analysis to determine workflow
        analysis = self._call_model(model, [
            {"role": "user", "content": f"Analyze this task and determine what type of workflow it needs: {task}"}
        ], "You are a workflow architect. Determine the optimal pipeline shape.")

        log.append({"phase": "analysis", "content": analysis[:300]})

        # Dynamic branching
        if "research" in analysis.lower() or "analyze" in analysis.lower():
            result = self._call_model(model, [{"role": "user", "content": f"Research and analyze: {task}"}])
            workflow_steps.append("research")
        elif "code" in analysis.lower() or "write" in analysis.lower():
            result = self._call_model(model, [{"role": "user", "content": f"Write code for: {task}"}])
            workflow_steps.append("code")
        elif "summarize" in analysis.lower() or "summar" in analysis.lower():
            result = self._call_model(model, [{"role": "user", "content": f"Summarize: {task}"}])
            workflow_steps.append("summarize")
        else:
            result = self._call_model(model, [{"role": "user", "content": task}])
            workflow_steps.append("direct")

        log.append({"phase": "execute", "workflow": workflow_steps, "content": result[:300]})

        # Check if more steps needed
        check = self._call_model(model, [
            {"role": "user", "content": f"Task: {task}\nResult so far: {result[:300]}\n\nIs this complete? If not, what next step?"}
        ], "You are a workflow controller.")

        if "NO" in check.upper() or "MORE" in check.upper():
            result2 = self._call_model(model, [
                {"role": "user", "content": f"Continue: {task}\nPrevious result: {result[:300]}\nNext step based on: {check[:200]}"}
            ])
            result += "\n" + result2[:300]
            workflow_steps.append("continuation")
            log.append({"phase": "continuation", "content": result2[:300]})

        return {"status": "complete", "output": result[:500], "workflow": workflow_steps, "log": log}

    def loop_13_goal_decomposition(self, model: str, task: str) -> Dict:
        """Pattern 13: Goal Decomposition Loop
        Break large goal into subgoals, subgoals into tasks, tasks into steps."""
        log = []

        # Decompose
        decomposition = self._call_model(model, [
            {"role": "user", "content": f"Decompose this goal into subgoals, then each subgoal into specific tasks:\n{task}"}
        ], "You are a goal decomposition engine. Break down until each unit is executable in one call.")

        log.append({"phase": "decompose", "content": decomposition[:500]})

        # Extract subgoals
        subgoals = re.findall(r'(?:Subgoal|Task|Step)\s*\d*[\.:\)]\s*([^\n]+)', decomposition)
        if not subgoals:
            subgoals = [task]

        results = []
        for i, subgoal in enumerate(subgoals[:8]):
            result = self._call_model(model, [{"role": "user", "content": f"Execute: {subgoal}"}])
            results.append({"subgoal": subgoal[:100], "result": result[:200]})
            log.append({"phase": f"execute_{i+1}", "subgoal": subgoal[:100], "result": result[:200]})

        # Synthesize
        synthesis = self._call_model(model, [
            {"role": "user", "content": f"Original goal: {task}\n\nResults from each subgoal:\n" + "\n".join(f"- {r['subgoal']}: {r['result'][:100]}" for r in results) + "\n\nSynthesize these into a final answer."}
        ])

        return {"status": "complete", "output": synthesis[:500], "subgoals": len(subgoals), "log": log}

    def loop_14_progress_evaluation(self, model: str, task: str, check_interval: int = 3) -> Dict:
        """Pattern 14: Progress Evaluation Loop
        Every N steps: stop and ask 'Are we getting closer to the goal?'"""
        log = []
        result = ""
        step = 0

        while step < 10:
            step += 1
            result = self._call_model(model, [
                {"role": "user", "content": f"Continue working on: {task}\nProgress so far: {result[:300] if result else 'Starting'}"}
            ])
            log.append({"step": step, "content": result[:200]})

            # Progress check every N steps
            if step % check_interval == 0:
                progress = self._call_model(model, [
                    {"role": "user", "content": f"Task: {task}\nCurrent state: {result[:300]}\n\nRate progress 0-100% and answer: Are we getting closer to the goal? Should we change strategy?"}
                ], "You are a progress evaluator.")
                log.append({"step": step, "phase": "evaluation", "content": progress[:200]})

                if "100%" in progress or "COMPLETE" in progress.upper():
                    return {"status": "complete", "output": result[:500], "steps": step, "log": log}

                if "CHANGE" in progress.upper() or "DIFFERENT" in progress.upper():
                    result = self._call_model(model, [
                        {"role": "user", "content": f"Change strategy for: {task}\nPrevious approach wasn't working. Try a completely different angle."}
                    ])
                    log.append({"step": step, "phase": "strategy_change", "content": result[:200]})

        return {"status": "complete", "output": result[:500], "steps": step, "log": log}

    def loop_15_constraint_satisfaction(self, model: str, task: str, constraints: List[str] = None) -> Dict:
        """Pattern 15: Constraint Satisfaction Loop
        Keep running until all constraints are met."""
        if not constraints:
            constraints = ["quality_above_threshold", "no_hallucinations", "complete_response"]

        log = []
        result = ""
        max_iterations = 10

        for iteration in range(1, max_iterations + 1):
            result = self._call_model(model, [
                {"role": "user", "content": f"{'Improve this to satisfy all constraints: ' + result[:300] if iteration > 1 else ''}Task: {task}\nConstraints: {', '.join(constraints)}"}
            ])
            log.append({"iteration": iteration, "content": result[:200]})

            # Check constraints
            check = self._call_model(model, [
                {"role": "user", "content": f"Check if ALL these constraints are met:\n{', '.join(constraints)}\n\nOutput:\n{result}\n\nAnswer PASS or FAIL for each."}
            ], "You are a constraint verifier.")

            log[iteration - 1]["check"] = check[:200]

            if "PASS" in check.upper() and "FAIL" not in check.upper():
                return {"status": "complete", "output": result[:500], "iterations": iteration, "log": log}

        return {"status": "best_effort", "output": result[:500], "iterations": max_iterations, "log": log}

    # ============================================================
    # CATEGORY 4 — EXPLORATION LOOPS
    # ============================================================

    def loop_16_branch_and_explore(self, model: str, task: str, approaches: List[str] = None) -> Dict:
        """Pattern 16: Branch-and-Explore Loop
        Explore multiple approaches simultaneously. Choose the best."""
        if not approaches:
            approaches = ["conservative", "aggressive", "creative"]

        log = []
        branches = []

        for approach in approaches:
            result = self._call_model(model, [
                {"role": "user", "content": f"Task: {task}\nApproach: {approach}. Be {approach} in your response."}
            ])
            branches.append({"approach": approach, "output": result[:300]})
            log.append({"phase": "branch", "approach": approach, "content": result[:200]})

        # Score each branch
        for branch in branches:
            score = self._call_model(model, [
                {"role": "user", "content": f"Rate this output 0.0-1.0:\n{branch['output']}"}
            ], "You are a judge. Return only a float.")
            try:
                branch["score"] = float(re.search(r'[\d.]+', score).group())
            except:
                branch["score"] = 0.5
            log.append({"phase": "score", "approach": branch["approach"], "score": branch["score"]})

        # Choose best
        best = max(branches, key=lambda b: b["score"])
        return {"status": "complete", "output": best["output"], "best_approach": best["approach"], "branches": branches, "log": log}

    def loop_17_tree_search(self, model: str, task: str, depth: int = 3, breadth: int = 3) -> Dict:
        """Pattern 17: Tree Search Loop
        Expand promising nodes. Prune weak ones. Search until solution found."""
        log = []
        nodes = [{"id": "root", "parent": None, "content": task, "score": 1.0, "depth": 0}]
        solutions = []

        for d in range(1, depth + 1):
            new_nodes = []
            for node in nodes:
                if node["depth"] != d - 1:
                    continue

                # Expand this node
                for b in range(breadth):
                    child = self._call_model(model, [
                        {"role": "user", "content": f"Task: {task}\nPath: {node['content'][:100]}\n\nExplore option {b+1} for this path."}
                    ])
                    child_id = f"{node['id']}_{b}"

                    # Score
                    score_text = self._call_model(model, [
                        {"role": "user", "content": f"Score this path 0.0-1.0:\n{child[:200]}"}
                    ], "You are a tree search evaluator.")
                    try:
                        score = float(re.search(r'[\d.]+', score_text).group())
                    except:
                        score = 0.5

                    new_nodes.append({"id": child_id, "parent": node["id"], "content": child[:200], "score": score, "depth": d})
                    log.append({"depth": d, "branch": b, "score": score, "content": child[:100]})

                    if score > 0.8:
                        solutions.append({"path": child_id, "content": child[:300], "score": score})

            # Prune: keep only top nodes
            new_nodes.sort(key=lambda n: n["score"], reverse=True)
            nodes.extend(new_nodes[:max(1, breadth // 2)])

            if solutions:
                best_solution = max(solutions, key=lambda s: s["score"])
                return {"status": "complete", "output": best_solution["content"], "depth": d, "solutions_found": len(solutions), "log": log}

        if solutions:
            best = max(solutions, key=lambda s: s["score"])
            return {"status": "complete", "output": best["content"], "depth": depth, "log": log}

        return {"status": "no_solution", "log": log}

    def loop_18_debate(self, model: str, topic: str, rounds: int = 3) -> Dict:
        """Pattern 18: Debate Loop
        Two agents argue opposite positions. Truth emerges through disagreement."""
        log = []
        pro_args = []
        con_args = []

        for round_num in range(1, rounds + 1):
            # Pro argument
            pro = self._call_model(model, [
                {"role": "user", "content": f"Round {round_num}. Argue FOR this position, addressing counterarguments:\nTopic: {topic}\n\nPrevious con arguments: {' | '.join(con_args[-2:]) if con_args else 'None'}"}
            ], "You are a debate champion arguing FOR the position. Be persuasive and rigorous.")
            pro_args.append(pro[:300])
            log.append({"round": round_num, "side": "pro", "content": pro[:200]})

            # Con argument
            con = self._call_model(model, [
                {"role": "user", "content": f"Round {round_num}. Argue AGAINST this position, addressing counterarguments:\nTopic: {topic}\n\nPrevious pro arguments: {' | '.join(pro_args[-2:]) if pro_args else 'None'}"}
            ], "You are a debate champion arguing AGAINST the position. Be persuasive and rigorous.")
            con_args.append(con[:300])
            log.append({"round": round_num, "side": "con", "content": con[:200]})

        # Synthesis
        synthesis = self._call_model(model, [
            {"role": "user", "content": f"Topic: {topic}\n\nArguments FOR:\n{' | '.join(pro_args)}\n\nArguments AGAINST:\n{' | '.join(con_args)}\n\nSynthesize the strongest position based on this debate."}
        ], "You are a judge. Synthesize the truth from both sides.")

        return {"status": "complete", "synthesis": synthesis[:500], "pro_arguments": pro_args, "con_arguments": con_args, "rounds": rounds, "log": log}

    # ============================================================
    # CATEGORY 5 — SYSTEM OPTIMIZATION LOOPS
    # ============================================================

    def loop_19_prompt_optimization(self, model: str, task: str, test_set: List[str] = None, max_iterations: int = 5) -> Dict:
        """Pattern 19: Prompt Optimization Loop
        Prompt rewrites itself based on where it fails."""
        if not test_set:
            test_set = [task]

        log = []
        current_prompt = f"Complete this task: {task}"
        best_prompt = current_prompt
        best_score = 0.0

        for iteration in range(1, max_iterations + 1):
            scores = []

            for test_item in test_set:
                result = self._call_model(model, [{"role": "user", "content": f"{current_prompt}\n\nInput: {test_item}"}])

                score_text = self._call_model(model, [
                    {"role": "user", "content": f"Score this output 0.0-1.0:\n{result[:300]}"}
                ], "You are a prompt evaluator.")
                try:
                    score = float(re.search(r'[\d.]+', score_text).group())
                except:
                    score = 0.5
                scores.append(score)

            avg_score = sum(scores) / len(scores)
            log.append({"iteration": iteration, "avg_score": avg_score, "prompt": current_prompt[:100]})

            if avg_score > best_score:
                best_score = avg_score
                best_prompt = current_prompt

            if avg_score >= 0.9:
                break

            # Improve prompt based on failures
            failures = [t for t, s in zip(test_set, scores) if s < 0.7]
            if failures:
                current_prompt = self._call_model(model, [
                    {"role": "user", "content": f"Current prompt: {current_prompt}\n\nIt failed on these inputs:\n{' | '.join(failures)}\n\nRewrite the prompt to fix these failures."}
                ], "You are a prompt engineer. Rewrite prompts to fix failure modes.")

        return {"status": "complete", "best_prompt": best_prompt[:200], "best_score": best_score, "iterations": iteration, "log": log}

    def loop_20_workflow_optimization(self, model: str, task: str) -> Dict:
        """Pattern 20: Workflow Optimization Loop
        The loop improves the loop. System measures and modifies its own workflow."""
        log = []
        start_time = time.time()

        # Run the task
        result = self._call_model(model, [{"role": "user", "content": task}])
        latency = time.time() - start_time

        # Measure
        quality_text = self._call_model(model, [
            {"role": "user", "content": f"Rate quality 0.0-1.0:\n{result[:300]}"}
        ], "You are a quality evaluator.")
        try:
            quality = float(re.search(r'[\d.]+', quality_text).group())
        except:
            quality = 0.5

        metrics = {
            "latency": round(latency, 2),
            "quality": quality,
            "tokens_estimate": len(result) // 4
        }

        self.workflow_metrics["latency"].append(metrics["latency"])
        self.workflow_metrics["quality"].append(metrics["quality"])
        self.workflow_metrics["cost"].append(metrics["tokens_estimate"])

        log.append({"phase": "measure", "metrics": metrics})

        # Optimize: suggest workflow improvements
        if len(self.workflow_metrics["latency"]) >= 3:
            avg_latency = sum(self.workflow_metrics["latency"][-3:]) / 3
            avg_quality = sum(self.workflow_metrics["quality"][-3:]) / 3

            optimization = ""
            if avg_latency > 30:
                optimization += "LATENCY: Consider parallelizing steps or using a smaller model. "
            if avg_quality < 0.7:
                optimization += "QUALITY: Add a critic loop before final output. "
            if metrics["tokens_estimate"] > 500:
                optimization += "COST: Consider token optimization."

            log.append({"phase": "optimize", "suggestion": optimization[:200]})

        return {
            "status": "complete",
            "output": result[:500],
            "metrics": metrics,
            "workflow_history": {k: v[-5:] for k, v in self.workflow_metrics.items()},
            "log": log
        }

    # ============================================================
    # MASTER LOOP CONTROLLER
    # ============================================================

    def run_loop(self, pattern: str, model: str, task: str, **kwargs) -> Dict:
        """Run any of the 20 loop patterns by name."""
        loop_map = {
            "1": self.loop_1_generate_critique_rewrite,
            "2": self.loop_2_score_and_retry,
            "3": self.loop_3_multi_critic,
            "4": self.loop_4_adversarial_critique,
            "5": self.loop_5_judge_ensemble,
            "6": self.loop_6_reflexion,
            "7": self.loop_7_memory_update,
            "8": self.loop_8_error_library,
            "9": self.loop_9_success_pattern,
            "10": self.loop_10_memory_compression,
            "11": self.loop_11_plan_execute_replan,
            "12": self.loop_12_dynamic_workflow,
            "13": self.loop_13_goal_decomposition,
            "14": self.loop_14_progress_evaluation,
            "15": self.loop_15_constraint_satisfaction,
            "16": self.loop_16_branch_and_explore,
            "17": self.loop_17_tree_search,
            "18": self.loop_18_debate,
            "19": self.loop_19_prompt_optimization,
            "20": self.loop_20_workflow_optimization,
            "generate_critique_rewrite": self.loop_1_generate_critique_rewrite,
            "score_retry": self.loop_2_score_and_retry,
            "multi_critic": self.loop_3_multi_critic,
            "adversarial": self.loop_4_adversarial_critique,
            "judge_ensemble": self.loop_5_judge_ensemble,
            "reflexion": self.loop_6_reflexion,
            "memory_update": self.loop_7_memory_update,
            "error_library": self.loop_8_error_library,
            "success_pattern": self.loop_9_success_pattern,
            "memory_compression": self.loop_10_memory_compression,
            "plan_execute_replan": self.loop_11_plan_execute_replan,
            "dynamic_workflow": self.loop_12_dynamic_workflow,
            "goal_decomposition": self.loop_13_goal_decomposition,
            "progress_evaluation": self.loop_14_progress_evaluation,
            "constraint_satisfaction": self.loop_15_constraint_satisfaction,
            "branch_explore": self.loop_16_branch_and_explore,
            "tree_search": self.loop_17_tree_search,
            "debate": self.loop_18_debate,
            "prompt_optimization": self.loop_19_prompt_optimization,
            "workflow_optimization": self.loop_20_workflow_optimization,
        }

        handler = loop_map.get(pattern)
        if not handler:
            return {"status": "error", "error": f"Unknown pattern: {pattern}. Available: 1-20 or by name."}

        return handler(model, task, **kwargs)

    def list_patterns(self) -> List[Dict]:
        """List all available loop patterns."""
        return [
            {"id": "1", "name": "Generate → Critique → Rewrite", "category": "Quality", "desc": "Generator produces output. Critic reviews. Generator rewrites."},
            {"id": "2", "name": "Score-and-Retry", "category": "Quality", "desc": "Generate. Score. Retry if below threshold."},
            {"id": "3", "name": "Multi-Critic", "category": "Quality", "desc": "Four critics evaluate independently. All must pass."},
            {"id": "4", "name": "Adversarial Critique", "category": "Quality", "desc": "Critic tries to break the answer. Generator defends."},
            {"id": "5", "name": "Judge Ensemble", "category": "Quality", "desc": "Multiple judges. Only high-consensus outputs advance."},
            {"id": "6", "name": "Reflexion", "category": "Memory", "desc": "Agent fails, analyzes why, stores lesson, retries."},
            {"id": "7", "name": "Memory Update", "category": "Memory", "desc": "Store decisions, outcomes, and lessons after each task."},
            {"id": "8", "name": "Error Library", "category": "Memory", "desc": "Search past failures before acting. Apply known fixes."},
            {"id": "9", "name": "Success Pattern", "category": "Memory", "desc": "Store and retrieve successful approaches."},
            {"id": "10", "name": "Memory Compression", "category": "Memory", "desc": "Compress many memories into higher-level abstractions."},
            {"id": "11", "name": "Plan → Execute → Replan", "category": "Planning", "desc": "Create plan, execute step, observe, update plan."},
            {"id": "12", "name": "Dynamic Workflow", "category": "Planning", "desc": "Pipeline decides its own shape at runtime."},
            {"id": "13", "name": "Goal Decomposition", "category": "Planning", "desc": "Break goals into subgoals, tasks, steps."},
            {"id": "14", "name": "Progress Evaluation", "category": "Planning", "desc": "Every N steps: are we getting closer to the goal?"},
            {"id": "15", "name": "Constraint Satisfaction", "category": "Planning", "desc": "Run until all constraints are met."},
            {"id": "16", "name": "Branch-and-Explore", "category": "Exploration", "desc": "Explore multiple approaches. Choose the best."},
            {"id": "17", "name": "Tree Search", "category": "Exploration", "desc": "Expand promising nodes. Prune weak ones."},
            {"id": "18", "name": "Debate", "category": "Exploration", "desc": "Two agents argue opposite positions."},
            {"id": "19", "name": "Prompt Optimization", "category": "System", "desc": "Prompt rewrites itself based on where it fails."},
            {"id": "20", "name": "Workflow Optimization", "category": "System", "desc": "The loop improves the loop. Self-redesign."},
        ]
