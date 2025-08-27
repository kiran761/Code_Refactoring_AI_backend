import httpx
from app.core.config import settings

async def _call_openai_api(prompt: str) -> str:
    """Private async function to call the OpenAI API."""
    headers = {
        "Content-Type": "application/json",
        "api-key": settings.GPT4_API_KEY
    }
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    # Use an async client with a longer timeout for LLM responses
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(settings.GPT4_API_URL, headers=headers, json=data)
            response.raise_for_status()
            
            content = response.json()["choices"][0]["message"]["content"]
            
            # Simple cleanup for markdown code blocks
            content = content.replace("```javascript", "").replace("```js", "").replace("```java", "").replace("```json", "").replace("```", "")
            return content.strip()
        except httpx.HTTPStatusError as e:
            # This now logs the detailed error from the API for better debugging
            print(f"OpenAI API error: {e.response.status_code} - {e.response.text}")
            raise Exception("Failed to refactor code due to an API error.")
        except Exception as e:
            print(f"An error occurred while calling OpenAI API: {e}")
            raise

async def refactor_java_code(old_code: str) -> str:
    """
    Creates a prompt to refactor Java code using modern standards.
    The prompt is phrased collaboratively to avoid content filters.
    """
    prompt = f"""
Please act as a senior Java Spring Boot developer. 
I would like your help to refactor the following legacy Java code.

The goal is to update it to modern Spring Boot (version 3.2.x or higher) and Java 21 standards. This includes using modern annotations, Jakarta EE, and constructor injection where applicable, while maintaining the original class and method names.

Please provide only the complete, refactored Java code without any extra explanations or markdown formatting.

Legacy Code to refactor:
```java
{old_code}
```
"""
    return await _call_openai_api(prompt)

async def refactor_nodejs_code(old_code: str, filename: str = "") -> str:
    """
    Creates a prompt to refactor Node.js or package.json files.
    The prompt is phrased collaboratively to avoid content filters.
    """
    if filename.endswith("package.json"):
        prompt = f"""
As an expert in Node.js package management, please update the dependency versions in this `package.json` file.

The objective is to bring all packages in `dependencies` and `devDependencies` to their latest stable versions compatible with Node.js 20+, while preserving existing version range symbols (^, ~). Please also ensure the file includes `"type": "module"` and an "engines" field for Node.js 20+.

Could you return only the updated, valid JSON content without any surrounding text or markdown?

Current `package.json`:
```json
{old_code}
```
"""
    else:
        prompt = f"""
As a senior Node.js developer, please refactor this JavaScript file to align with modern Node.js 20+ and ES2023 standards.

The main goal is to use modern syntax like ES Modules (import/export), async/await, const/let, and modern error handling. The original functionality should be preserved.

Could you provide only the refactored JavaScript code for this specific file, without any additional comments or explanations?

File to refactor: {filename}
```javascript
{old_code}
```
"""
    return await _call_openai_api(prompt)
