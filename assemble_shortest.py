import json

def main():
    with open('seq_all.json', 'r', encoding='utf-8') as infile:
        instances = json.load(infile)
    
    sorted_instances = sorted(instances, key=lambda instance: len(instance.get('actions', [])))    
    shortest_instances = sorted_instances[:100]
    
    with open('seq_shortest.json', 'w', encoding='utf-8') as outfile:
        json.dump(shortest_instances, outfile, indent=2)
    
    print("Filtered 100 shortest sequences into seq_shortest.json")

if __name__ == '__main__':
    main()