import json
import random

def main():
    with open('seq_all.json', 'r', encoding='utf-8') as infile:
        instances = json.load(infile)
    
    random_instances = random.sample(instances, min(50, len(instances)))
    
    with open('seq_random.json', 'w', encoding='utf-8') as outfile:
        json.dump(random_instances, outfile, indent=2)
    
    print("Filtered 100 random sequences into seq_random.json")

if __name__ == '__main__':
    main()
