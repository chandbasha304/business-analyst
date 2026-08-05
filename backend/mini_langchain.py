import re
import math
import os
from typing import List, Dict, Any, Optional, Tuple

try:
    import chromadb
    CHROMA_AVAILABLE = True
    EmbeddingBase = chromadb.EmbeddingFunction
except ImportError:
    CHROMA_AVAILABLE = False
    EmbeddingBase = object



class Document:
    def __init__(self, page_content: str, metadata: Optional[Dict[str, Any]] = None):
        self.page_content = page_content
        self.metadata = metadata or {}

    def __repr__(self):
        return f"Document(page_content='{self.page_content[:30]}...', metadata={self.metadata})"


class RecursiveCharacterTextSplitter:
    """Recursively splits text into character chunks with overlaps, keeping word boundaries if possible."""
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text: str) -> List[str]:
        chunks = []
        start = 0
        text_len = len(text)
        
        if text_len <= self.chunk_size:
            return [text]
            
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            
            # If we're not at the end, try to find a natural boundary (newline or space)
            if end < text_len:
                # Look back up to 50 chars for a newline
                nl_idx = text.rfind("\n", max(start, end - 50), end)
                if nl_idx != -1:
                    end = nl_idx + 1
                else:
                    # Look back for a space
                    sp_idx = text.rfind(" ", max(start, end - 20), end)
                    if sp_idx != -1:
                        end = sp_idx
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
                
            start = end - self.chunk_overlap
            if start >= text_len or end >= text_len:
                break
        return chunks

    def split_documents(self, documents: List[Document]) -> List[Document]:
        split_docs = []
        for doc in documents:
            chunks = self.split_text(doc.page_content)
            for i, chunk in enumerate(chunks):
                meta = doc.metadata.copy()
                meta["chunk_index"] = i
                split_docs.append(Document(page_content=chunk, metadata=meta))
        return split_docs


class TFIDFVectorStore:
    """Pure-Python TF-IDF vector database matching queries against stored document chunks."""
    def __init__(self):
        self.documents: List[Document] = []
        self.vocab: List[str] = []
        self.vectors: List[List[float]] = []
        self.idf: Dict[str, float] = {}
        self.stopwords = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", 
            "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being", 
            "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't", 
            "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
            "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", 
            "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", "here's", 
            "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", 
            "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", 
            "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", 
            "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", 
            "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", 
            "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", 
            "the", "their", "theirs", "them", "themselves", "then", "there", "there's", 
            "these", "they", "they'd", "they'll", "they're", "they've", "this", "those", 
            "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", 
            "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", 
            "when's", "where", "where's", "which", "while", "who", "who's", "whom", "why", 
            "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", 
            "you're", "you've", "your", "yours", "yourself", "yourselves"
        }

    def _tokenize(self, text: str) -> List[str]:
        # Convert to lowercase and find word boundaries
        words = re.findall(r'\b[a-z]{2,}\b', text.lower())
        return [w for w in words if w not in self.stopwords]

    def build_index(self, documents: List[Document]):
        """Builds TF-IDF index vocabulary and document vectors."""
        self.documents = list(documents)
        if not self.documents:
            self.vocab = []
            self.vectors = []
            self.idf = {}
            return
            
        # 1. Build Vocabulary and compute Document Frequencies (DF)
        df: Dict[str, int] = {}
        tokenized_docs = []
        
        for doc in self.documents:
            tokens = self._tokenize(doc.page_content)
            tokenized_docs.append(tokens)
            unique_tokens = set(tokens)
            for token in unique_tokens:
                df[token] = df.get(token, 0) + 1
                
        self.vocab = sorted(list(df.keys()))
        
        # 2. Compute IDF for each term
        total_docs = len(self.documents)
        self.idf = {}
        for term, count in df.items():
            # Standard IDF formula with smoothing to avoid divide-by-zero
            self.idf[term] = math.log((1 + total_docs) / (1 + count)) + 1.0
            
        # 3. Calculate TF-IDF vectors for all chunks
        self.vectors = []
        for tokens in tokenized_docs:
            vector = self._vectorize(tokens)
            self.vectors.append(vector)

    def _vectorize(self, tokens: List[str]) -> List[float]:
        """Converts token list to a normalized TF-IDF vector."""
        if not self.vocab:
            return []
            
        # Count term frequencies
        tf: Dict[str, int] = {}
        for token in tokens:
            if token in tf:
                tf[token] += 1
            else:
                tf[token] = 1
                
        # Generate TF-IDF weights
        vector = []
        squared_sum = 0.0
        for term in self.vocab:
            term_tf = tf.get(term, 0)
            weight = term_tf * self.idf.get(term, 0.0)
            vector.append(weight)
            squared_sum += weight * weight
            
        # L2 Normalize the vector to unit length
        norm = math.sqrt(squared_sum)
        if norm > 0:
            vector = [w / norm for w in vector]
            
        return vector

    def retrieve(self, query: str, k: int = 4, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[float, Document, str]]:
        """Retrieves top k documents matching query based on Cosine Similarity."""
        if not self.vectors or not self.vocab:
            return []
            
        query_tokens = self._tokenize(query)
        query_vector = self._vectorize(query_tokens)
        
        # Check if query vector is zero vector (no vocab overlap)
        if all(w == 0.0 for w in query_vector):
            # Fallback to simple sub-string matching
            matches = []
            for doc in self.documents:
                # Apply metadata filtering if specified
                if filter_metadata:
                    skip = False
                    for key, val in filter_metadata.items():
                        if doc.metadata.get(key) != val:
                            skip = True
                            break
                    if skip:
                        continue
                
                # Check for word overlaps
                overlap = sum(1 for q in query_tokens if q in doc.page_content.lower())
                if overlap > 0:
                    matches.append((float(overlap) / 10.0, doc, "Substring match"))
            matches.sort(key=lambda x: x[0], reverse=True)
            return matches[:k]
            
        scores = []
        for idx, doc in enumerate(self.documents):
            # Apply metadata filtering if specified
            if filter_metadata:
                skip = False
                for key, val in filter_metadata.items():
                    if doc.metadata.get(key) != val:
                        skip = True
                        break
                if skip:
                    continue
                    
            doc_vector = self.vectors[idx]
            
            # Cosine similarity is the dot product since vectors are pre-normalized
            dot_product = sum(query_vector[i] * doc_vector[i] for i in range(len(self.vocab)))
            
            # Generate reasoning trace math string
            term_matches = []
            for i, term in enumerate(self.vocab):
                if query_vector[i] > 0 and doc_vector[i] > 0:
                    term_matches.append(f"{term} ({query_vector[i]:.2f}*{doc_vector[i]:.2f})")
            
            math_formula = f"Cosine similarity dot-product = {dot_product:.3f} | Matches: " + (", ".join(term_matches) if term_matches else "None")
            
            if dot_product > 0.02:
                scores.append((dot_product, doc, math_formula))
                
        # Sort by similarity score descending
        scores.sort(key=lambda x: x[0], reverse=True)
        return scores[:k]


class ProjectLensEmbeddingFunction(EmbeddingBase):
    def __init__(self, api_key: str = ""):
        self.api_key = api_key

    def __call__(self, input: List[str]) -> List[List[float]]:
        if self.api_key:
            import httpx
            headers = {"Content-Type": "application/json"}
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-embedding-001:embedContent?key={self.api_key}"
            
            embeddings = []
            try:
                for text in input:
                    payload = {
                        "content": {
                            "parts": [{"text": text[:2048]}]
                        }
                    }
                    res = httpx.post(url, headers=headers, json=payload, timeout=10.0)
                    if res.status_code == 200:
                        val = res.json().get("embedding", {}).get("values", [])
                        if val:
                            embeddings.append(val)
                    else:
                        break
                
                if len(embeddings) == len(input):
                    return embeddings
            except Exception as e:
                pass
        
        # Local fallback: deterministic vectorizer
        return [self._local_vectorize(text) for text in input]

    def _local_vectorize(self, text: str, dimensions: int = 3072) -> List[float]:
        import hashlib
        import math
        vec = [0.0] * dimensions
        words = re.findall(r'\b[a-z]{2,}\b', text.lower())
        if not words:
            vec[0] = 1.0
            return vec
        for w in words:
            h = int(hashlib.md5(w.encode('utf-8')).hexdigest(), 16)
            idx = h % dimensions
            vec[idx] += 1.0
        # Normalise
        squared_sum = sum(x*x for x in vec)
        norm = math.sqrt(squared_sum)
        if norm > 0:
            vec = [x / norm for x in vec]
        return vec


class ChromaVectorStore:
    def __init__(self, persist_directory: str = "chroma_db", collection_name: str = "projectlens_v3_clean"):
        if not CHROMA_AVAILABLE:
            raise RuntimeError("Chroma DB is not available in this environment due to missing or blocked libraries.")
            
        self.persist_directory = os.path.join(os.path.dirname(os.path.dirname(__file__)), persist_directory)
        
        # Load API key for embedding generation if it exists in environment
        api_key = os.environ.get("GEMINI_API_KEY", "")
        # Parse from local .env if present
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        if not api_key and os.path.exists(env_path):
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        if k.strip() == "GEMINI_API_KEY":
                            api_key = v.strip()
                            break
        
        self.embedding_function = ProjectLensEmbeddingFunction(api_key=api_key)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.embedding_function,
            metadata={"hnsw:space": "cosine"}
        )

    def build_index(self, documents: List[Document]):
        """Clears collection and registers split documents into Chroma."""
        try:
            existing = self.collection.get()
            if existing and "ids" in existing and existing["ids"]:
                self.collection.delete(ids=existing["ids"])
        except Exception:
            try:
                self.collection = self.client.get_or_create_collection(
                    name="projectlens_docs",
                    embedding_function=self.embedding_function,
                    metadata={"hnsw:space": "cosine"}
                )
                existing = self.collection.get()
                if existing and "ids" in existing and existing["ids"]:
                    self.collection.delete(ids=existing["ids"])
            except Exception:
                pass

        if not documents:
            return

        ids = []
        texts = []
        metadatas = []
        
        for idx, doc in enumerate(documents):
            doc_id = f"doc_{idx}_{hash(doc.page_content[:30])}"
            meta = {}
            for k, v in doc.metadata.items():
                if isinstance(v, (str, int, float, bool)):
                    meta[k] = v
                else:
                    meta[k] = str(v)
            
            ids.append(doc_id)
            texts.append(doc.page_content)
            metadatas.append(meta)
            
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            self.collection.add(
                ids=ids[i:i+batch_size],
                documents=texts[i:i+batch_size],
                metadatas=metadatas[i:i+batch_size]
            )
            
        print(f"[ChromaStore] Index built successfully with {len(documents)} segments.")

    def retrieve(self, query: str, k: int = 4, filter_metadata: Optional[Dict[str, Any]] = None) -> List[Tuple[float, Document, str]]:
        """Queries the Chroma collection and returns tuples with similarity scores."""
        where = {}
        if filter_metadata:
            for key, val in filter_metadata.items():
                if isinstance(val, (str, int, float, bool)):
                    where[key] = val
                    
        where_clause = where if where else None
        
        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=where_clause,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            print(f"[ChromaStore Error] Query execution failed: {e}")
            return []

        retrieved = []
        if results and "documents" in results and results["documents"]:
            docs_list = results["documents"][0]
            metas_list = results["metadatas"][0] if "metadatas" in results else []
            distances_list = results["distances"][0] if "distances" in results else []
            
            for i in range(len(docs_list)):
                doc_text = docs_list[i]
                meta = metas_list[i] if i < len(metas_list) else {}
                distance = distances_list[i] if i < len(distances_list) else 0.0
                similarity = 1.0 / (1.0 + distance)
                
                doc_obj = Document(page_content=doc_text, metadata=meta)
                math_formula = f"Chroma Cosine Distance: {distance:.3f} | Estimated Similarity: {similarity:.3f}"
                retrieved.append((similarity, doc_obj, math_formula))
                
        return retrieved


