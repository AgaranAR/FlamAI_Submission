#!/usr/env/bin python3
import os
from datasets import load_dataset

def main():
    # We are using Muennighoff/flores200 as a mirror because facebook/flores is gated.
    # Note: Requires datasets<=2.18.0 to use trust_remote_code=True for this specific mirror.
    langs = ['eng_Latn', 'hin_Deva', 'tam_Taml', 'kan_Knda']
    
    os.makedirs('partA', exist_ok=True)
    
    for lang in langs:
        print(f'Downloading 100 lines for {lang}...')
        d = load_dataset('Muennighoff/flores200', lang, trust_remote_code=True)
        sentences = d['dev']['sentence'][:100]
        
        # Enforcing utf-8 encoding to avoid Windows cp1252 charmap errors
        with open(f'partA/{lang}.txt', 'w', encoding='utf-8') as f:
            for s in sentences:
                f.write(s.strip() + '\n')
                
    print("Corpus preparation complete!")

if __name__ == '__main__':
    main()
