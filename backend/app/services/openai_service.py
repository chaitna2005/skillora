"""
OpenAI Service
Handles AI question generation using OpenAI API

Can this app cover ages ~7 through college, all subjects?
----------------------------------------------------------------
**Yes, architecturally.** The product is topic-agnostic: the user prompt + ``difficulty_level``
drive age, subject, and rigor. The model must follow the JSON schema (4 options, verified flags).
Limitations are not “subjects” but **safety**, **local curriculum alignment**, and **factual
hallucination**—you should add teacher review for high-stakes use.

**Model picks (GPT-5.4 generation, 2025–2026 pricing tier)**

- **gpt-5.4** — Highest quality for hard STEM, multi-step logic, contest-style items, or when
  distractors must be airtight. Use with ``OPENAI_REASONING_EFFORT=medium`` or ``high`` (omit
  temperature; see ``_chat_completion_base_params``).
- **gpt-5.4-mini** — **Recommended default:** strong reasoning for most quizzes at much lower cost
  than full 5.4. Good for grades through college when prompts specify level.
- **gpt-5.4-nano** — High volume, simple recall/vocab quizzes; weaker on tricky proofs—use
  ``reasoning`` ``low`` or ``medium`` if quality is thin.

**Reasoning effort** (GPT-5.x only; set ``OPENAI_REASONING_EFFORT``): ``none`` (fastest; allows
``temperature``), ``low``, ``medium``, ``high``, ``xhard``. For **STEM / boolean / proofs**, use
``medium`` or ``high``. For **young kids / simple reading**, ``none`` + low temperature is often
enough. Per OpenAI: if reasoning is **not** ``none``, **do not** send ``temperature`` / ``top_p``.

**Reasoning values:** ``none`` | ``low`` | ``medium`` | ``high`` | ``xhigh`` (API spelling).

Older models (**gpt-4o**, **gpt-4o-mini**) still work: leave ``OPENAI_REASONING_EFFORT`` empty or
use a non–GPT-5 id and the client uses ``temperature`` + ``max_tokens`` only.

This service always emits **4 options per question** (RADIO = exactly one ``is_correct: true``;
CHECKLIST = one or more ``true``).
"""
from openai import OpenAI
import json
from typing import List, Dict, Any, Optional
from app.config import settings

# Initialize OpenAI client at module level to avoid initialization issues
_openai_client = None

def get_openai_client():
    """Get or create OpenAI client singleton"""
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
    return _openai_client


def _is_gpt5_family(model: str) -> bool:
    m = (model or "").lower()
    return "gpt-5" in m


def _chat_completion_base_params(
    *,
    max_completion_tokens: int,
    temperature: float = 0.2,
) -> Dict[str, Any]:
    """
    Build OpenAI Chat Completions kwargs for GPT-5.4 vs older models.

    GPT-5.4: ``reasoning.effort`` — only ``temperature`` when effort is ``none`` (API rule).
    """
    model = settings.OPENAI_MODEL
    effort_raw = getattr(settings, "OPENAI_REASONING_EFFORT", None)
    effort = (effort_raw or "").strip().lower() if effort_raw else ""

    params: Dict[str, Any] = {"model": model}

    if _is_gpt5_family(model):
        eff = effort if effort else "none"
        params["reasoning"] = {"effort": eff}
        if eff == "none":
            params["temperature"] = temperature
        params["max_completion_tokens"] = max_completion_tokens
    else:
        params["temperature"] = temperature
        params["max_tokens"] = max_completion_tokens

    return params


class OpenAIService:
    
    
    def __init__(self):
        # Use the module-level client
        self.client = get_openai_client()
    
    def generate_quiz_questions(
        self, 
        prompt: str, 
        difficulty_level: str, 
        total_questions: int
    ) -> List[Dict[str, Any]]:
        """
        Generate quiz questions based on prompt and difficulty
        
        Returns:
            List of questions with format:
            [
                {
                    "question_text": "...",
                    "question_type": "RADIO" | "CHECKLIST",
                    "options": [
                        {"option_text": "...", "is_correct": True/False},
                        ...
                    ]
                },
                ...
            ]
        """
        print(f"[OPENAI_SERVICE] Starting question generation")
        print(f"[OPENAI_SERVICE] Requested questions: {total_questions}")
        print(f"[OPENAI_SERVICE] Topic: {prompt}")
        print(f"[OPENAI_SERVICE] Difficulty: {difficulty_level}")
        
        system_prompt = """You are an expert quiz author. You output ONLY valid JSON.

Your output is consumed by software that requires OBJECTIVELY correct answers—not guesses, not
“closest” answers, and never a question where no option is truly correct.

## OUTPUT CONTRACT (NON-NEGOTIABLE)

1. EXACT question count: match the user’s requested number. No more, no less.

2. STRUCTURE: Every question has EXACTLY 4 options. Each option has:
   - "option_text" (string, the full answer text shown to the student)
   - "is_correct" (boolean true or false only—never null, never omit)

3. RADIO (single choice): EXACTLY ONE option has "is_correct": true; the other three MUST be false.
   That one true option must be the UNIQUE, OBJECTIVELY correct answer for the question stem.

4. CHECKLIST (multi select): AT LEAST ONE option has "is_correct": true; often two or more when the
   stem asks for “select all that apply.” Every "true" must be objectively correct; every "false" must
   be objectively wrong. If only one statement is true, prefer question_type "RADIO" instead.

5. JSON ONLY: no markdown, no prose outside JSON, no “answer key” appendix—put everything in the schema below.

## HOW YOU MUST BUILD EACH QUESTION (DO THIS IN ORDER—EVERY TIME)

For EVERY question, mentally run this pipeline BEFORE you write JSON:

**Step A — Understand the stem:** What exactly is being asked? (truth value, simplify, count,
equivalence, reading comprehension, etc.)

**Step B — Solve independently:** Compute or reason the correct result WITHOUT looking at your
options yet (evaluate expressions, build truth tables, simplify, recall facts).

**Step C — Map to options:** For each of the 4 option texts, decide TRUE or FALSE as a statement
about the problem. For RADIO, exactly one option must match your result from Step B.

**Step D — Verify distractors:** Each wrong option must be INCORRECT relative to Step B, not merely
“different wording.” For logic/math, double-check arithmetic and boolean rules (AND/OR/NOT/XOR,
operator precedence, edge cases 0/1, boundaries in “inclusive” ranges).

**Step E — Self-check before emitting:**
   - RADIO: sum of is_correct is exactly 1?
   - CHECKLIST: at least one true, and each true is correct?
   - No option is “correct” by accident (e.g. two options both right for a RADIO stem—if so, rewrite the stem or options) ?

If you cannot make four options with exactly one correct answer without ambiguity, CHANGE the
question or the numbers until you can. Never emit a sloppy stem.

## TOPIC-SPECIFIC RIGOR

- **Math / Boolean / logic / contests (e.g. ASCL-style):** Show the same rigor as in contest math:
  small numbers, unambiguous definitions, correct use of operators. Re-verify truth tables row by row.
- **Reading / vocabulary:** One option must match the text; distractors must be clearly wrong.
- **“Which is equivalent / which is true”:** Only one correct equivalence unless CHECKLIST is used
  and the stem explicitly allows multiple.

## INVALID OUTPUTS (DO NOT DO THESE)

- All four options false.
- RADIO with zero or two or more "is_correct": true.
- Marking an option true when another option is also correct for the same stem (RADIO).
- Correct answer missing from the four options (if so, replace one option with the correct answer).

## JSON SHAPE

{
  "questions": [
    {
      "question_text": "Clear, self-contained question?",
      "question_type": "RADIO",
      "options": [
        {"option_text": "...", "is_correct": false},
        {"option_text": "...", "is_correct": true},
        {"option_text": "...", "is_correct": false},
        {"option_text": "...", "is_correct": false}
      ]
    }
  ]
}
"""
        
        user_prompt = f"""Generate EXACTLY {total_questions} quiz questions.

USER TOPIC / INSTRUCTIONS (follow closely, but still obey the JSON contract and verification steps):
{prompt}

DIFFICULTY / LEVEL (from app): {difficulty_level}
REQUIRED QUESTION COUNT: {total_questions}

AUDIENCE AND SUBJECT COVERAGE (infer from topic + difficulty):
- This app is used from **early elementary through college** and **all subjects** (STEM, humanities,
  languages, arts, vocational, etc.). Match **reading level**, **vocabulary**, and **concept depth**
  to the difficulty and topic (e.g. age-appropriate wording for young learners; precise terminology
  for advanced / college prompts).
- Use **concrete, friendly examples** for younger students; **rigorous, technical** stems when the
  topic implies AP/undergraduate level.
- Any subject is allowed; stay **factually sound** and keep distractors clearly wrong.

Distribution (approximate):
- ~70% "question_type": "RADIO" (exactly one correct option per question)
- ~30% "question_type": "CHECKLIST" (multiple correct options where appropriate)

Rules:
1. Each question: exactly 4 options, each with "option_text" and boolean "is_correct".
2. For each question, SOLVE it first, then set flags—guaranteed correct answers at the level of the stem.
3. If the user asks for formats like “A–E” or five choices, ADAPT to this API: still output exactly
   four options; merge or rephrase so the best four remain unambiguous.
4. Do not add an answer key section; correctness is only in "is_correct".

Return JSON with key "questions" containing exactly {total_questions} items."""

        print(f"[OPENAI_SERVICE] System prompt length: {len(system_prompt)} characters")
        print(f"[OPENAI_SERVICE] User prompt length: {len(user_prompt)} characters")
        print(f"[OPENAI_SERVICE] Model: {settings.OPENAI_MODEL}")
        eff = getattr(settings, "OPENAI_REASONING_EFFORT", None)
        if _is_gpt5_family(settings.OPENAI_MODEL) and eff:
            print(f"[OPENAI_SERVICE] Reasoning effort: {eff}")

        content = None
        try:
            print(f"[OPENAI_SERVICE] Sending request to OpenAI API...")
            req = _chat_completion_base_params(max_completion_tokens=8000, temperature=0.2)
            req["messages"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
            req["response_format"] = {"type": "json_object"}
            response = self.client.chat.completions.create(**req)
            
            print(f"[OPENAI_SERVICE] Received response from OpenAI")
            print(f"[OPENAI_SERVICE] Response usage - prompt_tokens: {response.usage.prompt_tokens}, completion_tokens: {response.usage.completion_tokens}, total_tokens: {response.usage.total_tokens}")
            
            content = response.choices[0].message.content
            print(f"[OPENAI_SERVICE] Raw response content length: {len(content)} characters")
            print(f"[OPENAI_SERVICE] Raw response preview (first 500 chars): {content[:500]}")
            
            result = json.loads(content)
            print(f"[OPENAI_SERVICE] Successfully parsed JSON response")
            print(f"[OPENAI_SERVICE] JSON keys: {list(result.keys())}")
            
            # Validate and return questions
            questions = result.get("questions", [])
            print(f"[OPENAI_SERVICE] Questions found in response: {len(questions)}")
            print(f"[OPENAI_SERVICE] Expected questions: {total_questions}")
            
            if len(questions) != total_questions:
                print(f"[OPENAI_SERVICE] ERROR: Question count mismatch!")
                print(f"[OPENAI_SERVICE] Expected: {total_questions}, Got: {len(questions)}")
                print(f"[OPENAI_SERVICE] Difference: {total_questions - len(questions)}")
                # Log each question to see what we got
                for i, q in enumerate(questions):
                    q_text = q.get("question_text", "NO TEXT")[:100]
                    q_type = q.get("question_type", "NO TYPE")
                    q_options = len(q.get("options", []))
                    print(f"[OPENAI_SERVICE] Question {i+1}: type={q_type}, options={q_options}, text_preview='{q_text}'")
            else:
                print(f"[OPENAI_SERVICE] SUCCESS: Question count matches expected number!")
            
            # Validation
            print(f"[OPENAI_SERVICE] Starting validation of questions...")
            validated_count = 0
            for idx, q in enumerate(questions):
                try:
                    # Check required fields
                    if "question_text" not in q or "question_type" not in q or "options" not in q:
                        print(f"[OPENAI_SERVICE] ERROR: Question {idx+1} missing required fields")
                        print(f"[OPENAI_SERVICE] Question {idx+1} keys: {list(q.keys())}")
                        raise ValueError(f"Invalid question format from OpenAI - question {idx+1} missing required fields")
                    
                    # Validate question type
                    if q["question_type"] not in ["RADIO", "CHECKLIST"]:
                        print(f"[OPENAI_SERVICE] WARNING: Question {idx+1} has invalid type '{q['question_type']}', defaulting to RADIO")
                        q["question_type"] = "RADIO"  # Default fallback
                    
                    # Validate options count
                    options_count = len(q.get("options", []))
                    if options_count != 4:
                        print(f"[OPENAI_SERVICE] ERROR: Question {idx+1} has {options_count} options, expected 4")
                        raise ValueError(f"Question {idx+1} must have exactly 4 options, found {options_count}")
                    
                    # Validate each option has required fields and correct type
                    for opt_idx, opt in enumerate(q["options"]):
                        if "option_text" not in opt:
                            print(f"[OPENAI_SERVICE] ERROR: Question {idx+1}, Option {opt_idx+1} missing 'option_text'")
                            raise ValueError(f"Question {idx+1}, Option {opt_idx+1} missing 'option_text'")
                        
                        if "is_correct" not in opt:
                            print(f"[OPENAI_SERVICE] WARNING: Question {idx+1}, Option {opt_idx+1} missing 'is_correct', defaulting to false")
                            opt["is_correct"] = False
                        
                        # Ensure is_correct is boolean
                        if not isinstance(opt["is_correct"], bool):
                            print(f"[OPENAI_SERVICE] WARNING: Question {idx+1}, Option {opt_idx+1} has non-boolean is_correct value: {opt['is_correct']}")
                            # Convert to boolean
                            opt["is_correct"] = bool(opt["is_correct"])
                    
                    # CRITICAL: Ensure at least one correct answer
                    has_correct = any(opt.get("is_correct", False) for opt in q["options"])
                    if not has_correct:
                        print(f"[OPENAI_SERVICE] CRITICAL WARNING: Question {idx+1} has NO correct answer! AI did not mark any option as correct.")
                        print(f"[OPENAI_SERVICE] Question text: {q.get('question_text', '')[:100]}")
                        print(f"[OPENAI_SERVICE] Fixing by marking first option as correct")
                        q["options"][0]["is_correct"] = True
                    
                    # For RADIO type, ensure exactly one correct answer
                    if q["question_type"] == "RADIO":
                        correct_count = sum(1 for opt in q["options"] if opt.get("is_correct", False))
                        if correct_count != 1:
                            print(f"[OPENAI_SERVICE] WARNING: Question {idx+1} (RADIO) has {correct_count} correct answers, fixing to 1")
                            # Fix: keep first correct, set others to false
                            first_correct_found = False
                            for opt in q["options"]:
                                if opt.get("is_correct", False):
                                    if not first_correct_found:
                                        opt["is_correct"] = True
                                        first_correct_found = True
                                    else:
                                        opt["is_correct"] = False
                    
                    # For CHECKLIST type, ensure at least one correct answer
                    if q["question_type"] == "CHECKLIST":
                        correct_count = sum(1 for opt in q["options"] if opt.get("is_correct", False))
                        if correct_count == 0:
                            print(f"[OPENAI_SERVICE] WARNING: Question {idx+1} (CHECKLIST) has no correct answers, fixing")
                            q["options"][0]["is_correct"] = True
                    
                    validated_count += 1
                except Exception as e:
                    print(f"[OPENAI_SERVICE] ERROR validating question {idx+1}: {e}")
                    raise
            
            print(f"[OPENAI_SERVICE] Validation complete: {validated_count}/{len(questions)} questions validated")
            
            # CRITICAL: Ensure we have exactly the requested number of questions
            print(f"[OPENAI_SERVICE] Checking question count...")
            print(f"[OPENAI_SERVICE] Requested: {total_questions}")
            print(f"[OPENAI_SERVICE] Received from AI: {len(questions)}")
            
            if len(questions) < total_questions:
                error_msg = f"OpenAI returned {len(questions)} questions but {total_questions} were requested. Please try again or reduce the question count."
                print(f"[OPENAI_SERVICE] ERROR: {error_msg}")
                raise ValueError(error_msg)
            
            # Return exactly the requested number (slice in case AI returned more)
            final_questions = questions[:total_questions]
            print(f"[OPENAI_SERVICE] Returning exactly {len(final_questions)} questions")
            
            # Remove duplicates by question text (case-insensitive)
            seen_questions = set()
            unique_questions = []
            for q in final_questions:
                q_text_normalized = q.get("question_text", "").strip().lower()
                if q_text_normalized and q_text_normalized not in seen_questions:
                    seen_questions.add(q_text_normalized)
                    unique_questions.append(q)
                else:
                    print(f"[OPENAI_SERVICE] Duplicate question detected and removed: '{q.get('question_text', '')[:80]}'")
            
            print(f"[OPENAI_SERVICE] After deduplication: {len(unique_questions)} unique questions")
            
            if len(unique_questions) < total_questions:
                error_msg = f"After removing duplicates, only {len(unique_questions)} unique questions remain out of {total_questions} requested. Please try again."
                print(f"[OPENAI_SERVICE] ERROR: {error_msg}")
                raise ValueError(error_msg)
            
            return unique_questions[:total_questions]
                
        except json.JSONDecodeError as e:
            print(f"[OPENAI_SERVICE] ERROR: Failed to parse JSON response")
            print(f"[OPENAI_SERVICE] JSON Error: {e}")
            if content:
                print(f"[OPENAI_SERVICE] Response content that failed to parse (first 1000 chars): {content[:1000]}")
            else:
                print(f"[OPENAI_SERVICE] No content received from OpenAI")
            raise Exception(f"Failed to parse OpenAI response: {str(e)}")
                
        except Exception as e:
            print(f"[OPENAI_SERVICE] ERROR: Exception occurred during question generation")
            print(f"[OPENAI_SERVICE] Exception type: {type(e).__name__}")
            print(f"[OPENAI_SERVICE] Exception message: {str(e)}")
            import traceback
            print(f"[OPENAI_SERVICE] Traceback: {traceback.format_exc()}")
            raise Exception(f"Failed to generate questions: {str(e)}")
    
    def generate_quiz_name(self, prompt: str) -> str:
        """Generate a concise quiz name from the prompt"""
        try:
            req = _chat_completion_base_params(max_completion_tokens=64, temperature=0.5)
            req["messages"] = [
                {
                    "role": "system",
                    "content": (
                        "Generate a short, descriptive quiz title (max 5 words) from the given prompt. "
                        "Return only the title, nothing else."
                    ),
                },
                {"role": "user", "content": prompt},
            ]
            response = self.client.chat.completions.create(**req)
            
            raw = response.choices[0].message.content
            quiz_name = (raw or "").strip()
            return quiz_name if quiz_name else "General Quiz"
            
        except Exception as e:
            print(f"Quiz name generation error: {e}")
            # Fallback: use first few words of prompt
            words = prompt.split()[:3]
            return " ".join(words).title() + " Quiz"

