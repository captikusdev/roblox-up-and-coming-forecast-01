import json
import os
import sys

def main():
    input_dir = os.environ.get('MAKEFUN_INPUT_DIR', '/input')
    output_dir = os.environ.get('MAKEFUN_OUTPUT_DIR', '/output')
    
    history_path = os.path.join(input_dir, 'history.ndjson')
    output_path = os.path.join(output_dir, 'forecast.json')
    
    # Read last snapshot from history.ndjson
    last_snapshot = None
    try:
        with open(history_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    last_snapshot = json.loads(line)
    except FileNotFoundError:
        print(f"Error: {history_path} not found", file=sys.stderr)
        sys.exit(1)
        
    if not last_snapshot or 'up_and_coming' not in last_snapshot:
        print("Error: No up_and_coming data found in history", file=sys.stderr)
        sys.exit(1)
        
    # top10 = the last chart's 10 universe_ids in order
    top10_games = last_snapshot['up_and_coming'][:10]
    top10_ids = [game['universe_id'] for game in top10_games]
    
    # Spec: for each game g at place k in the LAST chart only:
    # p(g,k) += 0.30; p(g,k-1) += 0.12; p(g,k+1) += 0.12 (in-range only)
    # places are 1-indexed 1..10
    
    # probabilities: list of {"universe_id": int, "place": 1..10, "p": number}
    # We use a dict to accumulate: (universe_id, place) -> p
    probs_map = {}
    
    for k_zero, game in enumerate(top10_games):
        universe_id = game['universe_id']
        k = k_zero + 1 # 1-indexed place
        
        # Current place
        probs_map[(universe_id, k)] = probs_map.get((universe_id, k), 0.0) + 0.30
        
        # Previous place (if in range 1..10)
        if k - 1 >= 1:
            probs_map[(universe_id, k - 1)] = probs_map.get((universe_id, k - 1), 0.0) + 0.12
            
        # Next place (if in range 1..10)
        if k + 1 <= 10:
            probs_map[(universe_id, k + 1)] = probs_map.get((universe_id, k + 1), 0.0) + 0.12
            
    # Afterwards, if a place sums above 0.97 scale that place down to 0.97.
    # Group by place
    place_sums = {}
    for (_, place), p in probs_map.items():
        place_sums[place] = place_sums.get(place, 0.0) + p
        
    probabilities = []
    for (universe_id, place), p in probs_map.items():
        sum_p = place_sums[place]
        if sum_p > 0.97:
            p = p * (0.97 / sum_p)
        probabilities.append({
            "universe_id": universe_id,
            "place": place,
            "p": round(p, 6) # Rounding for deterministic and clean output
        })
        
    forecast = {
        "probabilities": probabilities,
        "top10": top10_ids
    }
    
    os.makedirs(output_dir, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(forecast, f)

if __name__ == "__main__":
    main()
