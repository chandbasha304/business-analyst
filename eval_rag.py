import sys
import json
from backend.agent import run_agent_pipeline

test_suite = [
    # --- POSITIVE TEST CASES ---
    {
        "id": "POS-01",
        "category": "Positive",
        "query": "Who is the Chief Power Systems Architect for Helios Solar Grid and what is their email?",
        "expected_facts": ["Dr. Robert Thorne", "r.thorne@helios-grid.io"]
    },
    {
        "id": "POS-02",
        "category": "Positive",
        "query": "What is the matching latency and hardware acceleration used by Quantum Trade Engine?",
        "expected_facts": ["sub-microsecond", "FPGA"]
    },
    {
        "id": "POS-03",
        "category": "Positive",
        "query": "What are the RTO and RPO benchmarks for Project Sentinel Disaster Recovery?",
        "expected_facts": ["15 minutes", "1 second"]
    },
    {
        "id": "POS-04",
        "category": "Positive",
        "query": "What compliance frameworks does BioHealth Clinical Engine follow for patient records?",
        "expected_facts": ["HIPAA", "HITECH", "GDPR"]
    },
    {
        "id": "POS-05",
        "category": "Positive",
        "query": "How many kilometers of subsea fiber does Project Neptune operate and how accurate is OTDR fault detection?",
        "expected_facts": ["38,000", "5 meters"]
    },
    {
        "id": "POS-06",
        "category": "Positive",
        "query": "What cryptographic algorithm and hardware vault does Project Aegis Cyber Vault use?",
        "expected_facts": ["quantum-resistant", "HSM"]
    },
    {
        "id": "POS-07",
        "category": "Positive",
        "query": "What heavy vehicles does Project Titan automate and what fuel reduction does it achieve?",
        "expected_facts": ["400-ton", "18%"]
    },
    {
        "id": "POS-08",
        "category": "Positive",
        "query": "Who is the CISO for CyberShield IAM and what SSO protocols are supported?",
        "expected_facts": ["Gabriel Thorne", "SAML 2.0"]
    },
    {
        "id": "POS-09",
        "category": "Positive",
        "query": "What is the total property portfolio valuation managed by Project Vantage Real Estate Analytics?",
        "expected_facts": ["$50 Billion"]
    },
    {
        "id": "POS-10",
        "category": "Positive",
        "query": "How many IoT sensors are integrated into Project Nexus Smart City Grid?",
        "expected_facts": ["50,000"]
    },
    {
        "id": "POS-11",
        "category": "Positive",
        "query": "How many freight containers does Chrono track and what is the ML bottleneck prediction accuracy?",
        "expected_facts": ["250,000", "94.8%"]
    },
    {
        "id": "POS-12",
        "category": "Positive",
        "query": "Who is the principal architect for Apex Cloud Native K8s and what service mesh is used?",
        "expected_facts": ["Siddharth Nair", "Istio"]
    },

    # --- NEGATIVE TEST CASES ---
    {
        "id": "NEG-01",
        "category": "Negative",
        "query": "What is the bluetooth pairing password for Helios Solar Inverters?",
        "expected_behavior": "missing_info"
    },
    {
        "id": "NEG-02",
        "category": "Negative",
        "query": "Who is the Vice President of Digital Marketing for Project Aegis Cyber Vault?",
        "expected_behavior": "missing_info"
    },

    # --- OUT OF BOX TEST CASES ---
    {
        "id": "OOB-01",
        "category": "Out-of-Box",
        "query": "What is the capital of India?",
        "expected_behavior": "out_of_scope"
    },
    {
        "id": "OOB-02",
        "category": "Out-of-Box",
        "query": "What is the current live price of Bitcoin?",
        "expected_behavior": "out_of_scope"
    },

    # --- MULTI-TURN CONVERSATION TEST CASES ---
    {
        "id": "MEM-01",
        "category": "Memory / Follow-up",
        "query": "Who is the lead for Project Helios Solar Grid?",
        "follow_up_query": "What is his email and designated role?",
        "expected_facts": ["r.thorne@helios-grid.io", "Chief Power Systems Architect"]
    }
]

def run_automated_eval():
    print("==========================================================================================")
    print("              AUTOMATED RAG ACCURACY & GROUNDING BENCHMARK EVALUATION                     ")
    print("==========================================================================================\n")
    
    passed = 0
    failed = 0
    total = len(test_suite)
    
    for item in test_suite:
        t_id = item["id"]
        cat = item["category"]
        q = item["query"]
        
        print(f"[{t_id}] Testing Query: '{q}'")
        
        if cat == "Memory / Follow-up":
            r1 = run_agent_pipeline(q, [], "admin", "Admin")
            history = [{"user": q, "ai": r1["answer"]}]
            follow_q = item["follow_up_query"]
            print(f"   -> Follow-up Query: '{follow_q}'")
            res = run_agent_pipeline(follow_q, history, "admin", "Admin")
        else:
            res = run_agent_pipeline(q, [], "admin", "Admin")

        answer = res.get("answer", "")
        is_pass = False
        reason = ""

        if cat == "Positive" or cat == "Memory / Follow-up":
            matched_facts = [f for f in item["expected_facts"] if f.lower() in answer.lower()]
            if len(matched_facts) == len(item["expected_facts"]):
                is_pass = True
                reason = f"All {len(matched_facts)} expected facts matched accurately."
            else:
                missing = [f for f in item["expected_facts"] if f.lower() not in answer.lower()]
                reason = f"Missing expected facts: {missing}"

        elif cat == "Negative":
            if "does not contain" in answer.lower() or "missing" in answer.lower() or "outside" in answer.lower():
                is_pass = True
                reason = "Correctly detected unindexed/missing details without hallucinating."
            else:
                reason = f"Failed negative constraint. Output: {answer[:100]}"

        elif cat == "Out-of-Box":
            if "outside the scope" in answer.lower() or "enterprise knowledge assistant" in answer.lower():
                is_pass = True
                reason = "Correctly rejected out-of-scope general trivia question."
            else:
                reason = f"Failed out-of-scope constraint. Output: {answer[:100]}"

        if is_pass:
            passed += 1
            print(f"   ===> STATUS: [PASS] | {reason}\n")
        else:
            failed += 1
            print(f"   ===> STATUS: [FAIL] | {reason}\n")

    acc_score = (passed / total) * 100
    print("==========================================================================================")
    print(f"                        FINAL ACCURACY BENCHMARK EVALUATION SUMMARY                       ")
    print("==========================================================================================")
    print(f"Total Evaluated Test Cases : {total}")
    print(f"Passed Test Cases          : {passed}")
    print(f"Failed Test Cases          : {failed}")
    print(f"OVERALL SYSTEM ACCURACY    : {acc_score:.2f}%")
    print("==========================================================================================\n")

if __name__ == "__main__":
    run_automated_eval()
