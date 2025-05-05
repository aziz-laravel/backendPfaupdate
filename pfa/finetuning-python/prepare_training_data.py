import json

# Lire le fichier training_data.jsonl
examples = []
with open('training_data.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        examples.append(json.loads(line))

print(f"Nombre d'exemples chargés : {len(examples)}")

# Créer le Modelfile
with open('Modelfile', 'w', encoding='utf-8') as f:
    # Base du modèle
    f.write("FROM codellama\n\n")
    
    # Paramètres
    f.write("# Paramètres du modèle\n")
    f.write("PARAMETER temperature 0.7\n")
    f.write("PARAMETER top_p 0.9\n")
    f.write("PARAMETER stop \"</s>\"\n\n")
    
    # Système
    f.write("# Système : Définition de l'assistant\n")
    f.write("SYSTEM \"Tu es un assistant spécialisé en programmation Python, machine learning et data science. ")
    f.write("Tu fournis des réponses précises, correctes et bien formatées.\"\n\n")
    
    # Ajouter les exemples (limiter à 50 pour commencer - réduire pour tester)
    f.write("# Exemples d'apprentissage\n")
    max_examples = min(50, len(examples))  # Limiter à 50 exemples pour tester d'abord
    
    for i in range(max_examples):
        example = examples[i]
        # Utiliser des guillemets simples pour éviter les problèmes d'échappement
        user_prompt = example.get('prompt', '').replace('"', '\\"').replace('\n', '\\n')
        assistant_completion = example.get('completion', '').replace('"', '\\"').replace('\n', '\\n')
        
        f.write(f'MESSAGE role=user "{user_prompt}"\n')
        f.write(f'MESSAGE role=assistant "{assistant_completion}"\n\n')

print(f"{max_examples} exemples d'entraînement ont été ajoutés au Modelfile.")