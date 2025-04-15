from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
import os
import re
import subprocess
import pandas as pd
import io
import traceback

def index(request):
    return render(request, 'pages/index.html')

@csrf_exempt
def generate_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            prompt = data.get('prompt', '')
            csv_content = data.get('csv', '')  # Récupération du CSV
            
            if not prompt:
                return JsonResponse({'error': 'No prompt provided'}, status=400)
            
            # Traitement du CSV avec plusieurs méthodes pour gérer différents formats
            csv_preview = "Aucune donnée CSV fournie."
            df = None
            
            if csv_content:
                try:
                    # Méthode 1: Lecture standard avec pandas
                    df = pd.read_csv(io.StringIO(csv_content))
                    csv_preview = df.head(5).to_string(index=False)
                except Exception as e1:
                    try:
                        # Méthode 2: Essai avec différents séparateurs
                        for sep in [',', ';', '\t', ' ']:
                            try:
                                df = pd.read_csv(io.StringIO(csv_content), sep=sep)
                                if len(df.columns) > 1:  # Si nous avons plus d'une colonne, c'est probablement bon
                                    csv_preview = df.head(5).to_string(index=False)
                                    break
                            except:
                                continue
                        
                        # Si toujours pas de dataframe valide
                        if df is None or len(df.columns) <= 1:
                            # Méthode 3: Format personnalisé (comme votre exemple avec Setosa)
                            lines = csv_content.strip().split('\n')
                            all_entries = []
                            
                            for line in lines:
                                entries = line.strip().split()
                                for entry in entries:
                                    parts = entry.split(',')
                                    if len(parts) >= 2:  # Au moins 2 éléments pour que ce soit utile
                                        all_entries.append(parts)
                            
                            if all_entries:
                                # Détecter le nombre maximum de colonnes
                                max_cols = max(len(entry) for entry in all_entries)
                                # Générer des noms de colonnes génériques
                                columns = [f'col_{i}' for i in range(max_cols)]
                                
                                # Normaliser la longueur des entrées
                                normalized_entries = []
                                for entry in all_entries:
                                    if len(entry) < max_cols:
                                        entry = entry + [''] * (max_cols - len(entry))
                                    normalized_entries.append(entry)
                                
                                df = pd.DataFrame(normalized_entries, columns=columns)
                                csv_preview = df.head(5).to_string(index=False)
                    except Exception as e2:
                        csv_preview = f"Erreur lors de la lecture du CSV : Format non reconnu. Détails: {str(e1)}, {str(e2)}"
            
            # Information sur le dataframe pour le modèle
            df_info = ""
            if df is not None:
                df_info = f"""
Informations sur le DataFrame:
- Nombre de lignes: {df.shape[0]}
- Nombre de colonnes: {df.shape[1]}
- Noms des colonnes: {', '.join(df.columns.tolist())}
- Types de données: 
{df.dtypes.to_string()}
"""
            
            # Génération du prompt complet avec des conseils pour traiter le CSV
            full_prompt = f"""
Écris du code Python pour résoudre le problème suivant :
{prompt}

Voici un aperçu des données CSV fournies :
{csv_preview}

{df_info}

Instructions supplémentaires:
1. Assure-toi que le code gère correctement le format spécifique du CSV.
2. Vérifie et nettoie les données avant le traitement (valeurs manquantes, types, etc.).
3. Utilise pandas pour les manipulations de données.
4. Inclus des visualisations si pertinent (matplotlib, seaborn).
5. Le code doit être fonctionnel, bien commenté et efficace.
"""

            # Exécuter Ollama pour générer le code
            result = subprocess.run(
                ['ollama', 'run', 'codellama', full_prompt],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=240
            )

            if result.returncode != 0:
                return JsonResponse({'error': 'Ollama execution failed', 'details': result.stderr}, status=500)

            response_text = result.stdout.strip()

            # Extraction du code
            code_pattern = r"```python\s*(.*?)\s*```"
            code_match = re.search(code_pattern, response_text, re.DOTALL)
            clean_code = code_match.group(1) if code_match else response_text

            # Ajouter des imports standards pour le traitement de données si manquants
            standard_imports = [
                "import pandas as pd",
                "import numpy as np",
                "import matplotlib.pyplot as plt",
                "import seaborn as sns"
            ]
            
            for imp in standard_imports:
                if imp not in clean_code:
                    clean_code = imp + "\n" + clean_code

            return JsonResponse({'response': clean_code})

        except Exception as e:
            # Capture complète de l'erreur pour le débogage
            error_details = traceback.format_exc()
            return JsonResponse({
                'error': 'Processing failed', 
                'details': str(e),
                'traceback': error_details
            }, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)