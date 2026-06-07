from llama_cpp import Llama

# Lazy load model to avoid blocking on import
_llm = None

def get_llm():
    """Lazy load the Mistral model on first use"""
    global _llm
    if _llm is None:
        _llm = Llama(
            model_path="model/mistral-7b-instruct-v0.2.Q4_K_M.gguf",
            n_ctx=4096,
            n_threads=4,
            verbose=False
        )
    return _llm

# For backward compatibility, create a property-like access
class LazyLLM:
    def __call__(self, *args, **kwargs):
        return get_llm()(*args, **kwargs)
    
    def __getattr__(self, name):
        return getattr(get_llm(), name)

llm = LazyLLM()