import requests
from bs4 import BeautifulSoup
import openai

# Step 1: Search Google Custom Search and fetch full content
def google_search_with_full_content(query, api_key, cse_id):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": api_key,
        "cx": cse_id,
        "num": 5  # Number of results
    }
    response = requests.get(url, params=params)
    results = response.json()
    items = results.get('items', [])
    search_results = []
    print("Got responses: ")
    for item in items:
        snippet = item.get('snippet', '')
        link = item.get('link', '')
        full_text = fetch_full_text(link)
        search_results.append({
            'title': item.get('title', ''),
            'link': link,
            'snippet': snippet,
            'full_text': full_text
        })
    return search_results

def fetch_full_text(url):
    try:
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(response.text, 'html.parser')
        # Get all visible text
        text = soup.get_text(separator='\n', strip=True)
        # Optionally, limit to first 2000 characters to avoid huge prompts
        # return text[:2000]
        return text
    except Exception as e:
        return f"Error fetching {url}: {e}"

# Step 2: Send results to Azure OpenAI
def ask_azure_openai(prompt, azure_endpoint, azure_api_key, deployment_name):
    headers = {
        "api-key": azure_api_key,
        "Content-Type": "application/json"
    }
    data = {
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    url = f"{azure_endpoint}/openai/deployments/{deployment_name}/chat/completions?api-version=2024-02-15-preview"
    response = requests.post(url, headers=headers, json=data)
    return response.json()["choices"][0]["message"]["content"]

# Usage
GOOGLE_API_KEY = "AIzaSyC2XD5jyl_tCs9b0h0tHwPXvbCy6TlrYNI"
GOOGLE_CSE_ID = "12b0c23528bcf42a3"
AZURE_ENDPOINT = "https://ngtdazureaihub1570085143.services.ai.azure.com/"
AZURE_API_KEY = "8EHWQ96vkKRQwmFIlS3EvmL5fNdLxN5A4oFPm4WY1R64gzcGcZxNJQQJ99BDACHrzpqXJ3w3AAAAACOGA3wK"
DEPLOYMENT_NAME = "gpt-4o"
query = "Provide a python code to connect generate_and_retrieve of amazon aws bedrock with Arize."

search_results = google_search_with_full_content(query, GOOGLE_API_KEY, GOOGLE_CSE_ID)

# Combine all full_texts for the prompt (be mindful of token limits!)
combined_text = "\n\n".join(
    f"Title: {item['title']}\nURL: {item['link']}\nContent: {item['full_text']}" for item in search_results
)

prompt = f"Based on the following web search results, answer the question: {query}\n\n{combined_text}"
answer = ask_azure_openai(prompt, AZURE_ENDPOINT, AZURE_API_KEY, DEPLOYMENT_NAME)

print(combined_text)
print("\n---\n")
print(answer)