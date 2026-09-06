
import tiktoken
enc = tiktoken.get_encoding('gpt2')
with open('partA/eng_Latn.txt', 'r', encoding='utf-8') as f:
    sents = f.readlines()[:10]
norm = sum(len(enc.encode(s.strip())) for s in sents if s.strip())
low = sum(len(enc.encode(s.strip().lower())) for s in sents if s.strip())
print(f'10 lines from A1 corpus -> normal: {norm}, lower: {low}')

