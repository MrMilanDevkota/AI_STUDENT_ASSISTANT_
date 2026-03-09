"""
Chat Engine Service
Implements a RAG (Retrieval-Augmented Generation) pipeline for
answering student questions based on their uploaded documents.

Pipeline:
1. User asks a question
2. Retrieve relevant chunks from FAISS vector store
3. Combine chunks as context
4. Send context + question to Gemini LLM
5. Return grounded answer
"""

import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# System prompt that defines the AI tutor persona
SYSTEM_PROMPT = """You are a helpful AI study tutor. Your role is to help students understand their study materials.

IMPORTANT RULES:
1. ONLY answer based on the provided context from the student's documents
2. If the answer is not in the context, say: "I don't see information about that in your study material. Please check your notes."
3. Be clear, educational, and encouraging
4. Break down complex concepts into simple terms
5. If appropriate, suggest related topics from the material the student might want to review
6. Never make up information not present in the context
"""


def answer_question(
    question: str,
    vector_store_path: str,
    chat_history: List[Dict] = None,
    k: int = 5
) -> str:
    """
    Answer a student's question using RAG pipeline.

    Args:
        question: The student's question.
        vector_store_path: Path to FAISS index for this document.
        chat_history: Previous messages for context (list of {role, content} dicts).
        k: Number of relevant chunks to retrieve.

    Returns:
        AI-generated answer string grounded in document content.
    """
    try:
        from langchain.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from .vector_store import retrieve_relevant_chunks
        from .llm import get_llm

        # Step 1: Retrieve relevant context chunks
        relevant_chunks = retrieve_relevant_chunks(
            vector_store_path=vector_store_path,
            query=question,
            k=k
        )

        if not relevant_chunks:
            return "I couldn't find relevant information in your study material for this question."

        # Step 2: Combine chunks into context string
        context = "\n\n---\n\n".join(relevant_chunks)

        # Step 3: Build conversation history string
        history_text = ""
        if chat_history:
            history_parts = []
            for msg in chat_history[-6:]:  # Keep last 6 messages for context
                role = "Student" if msg['role'] == 'user' else "Tutor"
                history_parts.append(f"{role}: {msg['content']}")
            history_text = "\n".join(history_parts)

        # Step 4: Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            ("human", """Here is the relevant content from the student's study material:

--- STUDY MATERIAL CONTEXT ---
{context}
--- END CONTEXT ---

{history_section}

Student's Question: {question}

Please provide a helpful, accurate answer based ONLY on the context above:""")
        ])

        # Step 5: Generate answer
        llm = get_llm(temperature=0.2)
        chain = prompt | llm | StrOutputParser()

        history_section = ""
        if history_text:
            history_section = f"Previous conversation:\n{history_text}\n"

        answer = chain.invoke({
            "context": context,
            "question": question,
            "history_section": history_section,
        })

        logger.info(f"Generated answer for question: '{question[:50]}...'")
        return answer.strip()

    except Exception as e:
        logger.error(f"Chat engine error: {e}")
        raise


def get_study_tips(text: str) -> str:
    """
    Generate personalized study tips based on the document content.

    Args:
        text: Document text sample.

    Returns:
        Study tips and suggestions.
    """
    try:
        from langchain.prompts import PromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        from .llm import get_llm

        llm = get_llm(temperature=0.4)

        prompt = PromptTemplate(
            input_variables=["text"],
            template="""Based on the following study material, provide 5 specific study tips
to help a student effectively learn and retain this content.

Study Material Sample:
{text}

Provide practical, specific tips for studying THIS material:"""
        )

        chain = prompt | llm | StrOutputParser()
        text_sample = text[:5000] if len(text) > 5000 else text
        result = chain.invoke({"text": text_sample})

        return result.strip()

    except Exception as e:
        logger.error(f"Study tips generation failed: {e}")
        raise
