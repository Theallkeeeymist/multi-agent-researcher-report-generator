import time
import requests
import streamlit as st

def fetch_research_report(api_url: str, question: str, status_placeholder):
    """Sends the prompt and polls the backend until completion."""
    try:
        # 1. Dispatch the task
        init_response = requests.post(api_url, json={"question": question}, timeout=10)
        init_response.raise_for_status()
        task_id = init_response.json()["task_id"]

        # 2. Poll for status
        base_url = api_url.replace("/research", "")
        status_url = f"{base_url}/research/status/{task_id}"

        while True:
            status_response = requests.get(status_url, timeout=10)
            status_response.raise_for_status()
            current_status = status_response.json()

            if current_status["status"] == "Completed":
                status_placeholder.empty()
                return current_status["result"], None
            elif current_status["status"] == "Failed":
                status_placeholder.empty()
                return None, f"Worker error: {current_status.get('error')}"
            else:
                status_placeholder.markdown(
                    f'<p class="eyebrow" style="justify-content: center;"><span class="dot"></span> Status: {current_status["status"]}...</p>', 
                    unsafe_allow_html=True
                )
                time.sleep(3)

    except requests.exceptions.ConnectionError:
        return None, f"Can't reach the backend at {api_url}. Confirm Docker is running."
    except requests.exceptions.Timeout:
        return None, "API timed out while checking status."
    except Exception as e:
        return None, f"Backend error: {str(e)}"