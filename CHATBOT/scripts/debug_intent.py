from LGU.chat import ChatBot
import sys

q = sys.argv[1] if len(sys.argv) > 1 else "what fee structure of lgu"
print("Query:", q)
bot = ChatBot()

# get embedding and pattern embeddings
try:
    import numpy as np
    user_emb = bot.get_embedding(q)
    pattern_embs = np.array(bot.pattern_embeddings)
    # compute cosine similarity correctly: dot / (||a|| * ||b||)
    user_norm = np.linalg.norm(user_emb) + 1e-12
    pattern_norms = np.linalg.norm(pattern_embs, axis=1) + 1e-12
    sims = (pattern_embs @ user_emb) / (pattern_norms * user_norm)
except Exception as e:
    print("Error computing sims:", e)
    sims = None

if sims is not None:
    import numpy as np
    idxs = np.argsort(-sims)[:10]
    print("Top semantic matches:")
    for i in idxs:
        pat, tag = bot.pattern_list[i]
        print(f"  sim={float(sims[i]):.4f} tag={tag} pattern={pat}")

print("\nget_best_answer result:\n")
print(bot.get_best_answer(q))

# Also show fallback embeddings similarity
try:
    user_emb_b = bot.get_embedding(q).reshape(1,-1)
    sims2 = np.dot(bot.question_embeddings, user_emb_b.T).flatten()
    best_idx2 = int(sims2.argmax())
    print('\nFallback embedding top pattern:', bot.pattern_list[best_idx2], 'sim=', float(sims2[best_idx2]))
except Exception:
    pass
