import requests

URL = "https://smt.esante.gouv.fr/fhir/CodeSystem/TRE-A02-ProfessionSavFaire-CISIS"

def fetch_codes():
    """
    Télécharge la nomenclature TRE-A02 et construit un dict :
    code -> libellé.
    Gère aussi les codes abrégés (ex : SM08 -> 08).
    """
    resp = requests.get(URL)
    resp.raise_for_status()
    data = resp.json()

    codes = {}

    for entry in data.get("concept", []):
        code = entry.get("code")
        display = entry.get("display")

        if not code or not display:
            continue

        # Code complet
        codes[code] = display

        # Gestion des codes de type "G15_10/SM08"
        if "/" in code:
            _, short = code.split("/", 1)  # "SM08"
            codes[short] = display         # SM08

            # Si le code commence par SM, on crée la version courte "08"
            if short.startswith("SM") and len(short) > 2:
                bare = short[2:]
                codes[bare] = display      # "08"

    return codes


# ⬇️ La fonction simple que tu vas utiliser partout
def get_spe(code: str):
    """
    Retourne la spécialité correspondant à un code (08, SM08, etc.)
    Exemple : get_spe("08"), get_spe("SM08")
    """
    code = code.strip()

    # On charge une seule fois (lazy loading)
    if not hasattr(get_spe, "codes_dict"):
        get_spe.codes_dict = fetch_codes()

    d = get_spe.codes_dict
    return d.get(code, d.get(code.upper(), f"Code {code} non trouvé"))

if __name__ == "__main__":
    print(get_spe("48"))  # Test rapide