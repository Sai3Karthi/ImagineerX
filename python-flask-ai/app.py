import vertexai
from vertexai.preview.generative_models import GenerativeModel

def summarize_reviews(prompt):
    try:
        vertexai.init(project="iron-burner-412609", location="us-central1")

        model = GenerativeModel("gemini-pro-vision")

        responses = model.generate_content(
            prompt,
            generation_config={
                "max_output_tokens": 2048,
                "temperature": 0.4,
                "top_p": 1,
                "top_k": 32
            },
            stream=True
        )

        generated_output = ""
        for response in responses:
            generated_output += response.text + "\n"

        return generated_output

    except Exception as e:
        print(f"Error occurred: {e}")
        return ""

if __name__ == "__main__":
    user_prompt = input("Enter your prompt: ")

    if user_prompt.strip():
        print(summarize_reviews(user_prompt))
    else:
        print("Prompt cannot be empty.")