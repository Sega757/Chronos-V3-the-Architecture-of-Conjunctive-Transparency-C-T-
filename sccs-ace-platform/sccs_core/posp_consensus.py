import psycopg2
import os
import datetime

class PoSPArbiter:
    """
    Proof of Sampling (PoSP) Game-Theoretic Consensus Arbiter.
    Enforces Pure-Strategy Nash Equilibrium (E[U_cheat] < 0).
    """
    def __init__(self, cost_c=1.0, reward_r=10.0, stake_s=100.0, adversary_ratio_r=0.1):
        self.C = cost_c
        self.R = reward_r
        self.S = stake_s
        self.r = adversary_ratio_r

        self.db_url = os.environ.get('DATABASE_URL', 'postgresql://sccs_user:sccs_password@postgres:5432/sccs_db')

    def _get_db_connection(self):
        try:
            conn = psycopg2.connect(self.db_url)
            return conn
        except Exception as e:
            print(f"Warning: Could not connect to DB for PoSP: {e}")
            return None

    def calculate_challenge_probability(self):
        numerator = self.C * (1.0 - self.r)
        denominator = self.R + self.S

        if denominator == 0:
            return 1.0

        p_min = numerator / denominator
        p_enforced = min(1.0, p_min + 0.01)
        return p_enforced

    def trigger_challenge(self, p_threshold):
        import random
        roll = random.random()
        return roll <= p_threshold

    def slash_stake(self, node_id, reason="Reasoning trace discrepancy / Huber bounds exceeded"):
        print(f"SLASHING EXECUTED: Node {node_id} burned {self.S} stake.")
        conn = self._get_db_connection()
        if conn:
            try:
                cur = conn.cursor()
                query = """
                INSERT INTO generation_logs (model_used, prompt_hash, prompt_text, response_text, execution_time_ms, status, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

                import hashlib
                phash = hashlib.sha256(f"slash_{node_id}".encode()).hexdigest()

                cur.execute(query, (
                    "Arbiter_PoSP_Engine",
                    phash,
                    f"Audit of node {node_id}",
                    f"SLASHED: {self.S} stake burned. Reason: {reason}",
                    0,
                    "error",
                    datetime.datetime.now()
                ))
                conn.commit()
                cur.close()
            except Exception as e:
                print(f"Error logging slash to DB: {e}")
            finally:
                conn.close()
        else:
            with open("slashing_audit.log", "a") as f:
                f.write(f"[{datetime.datetime.now()}] SLASHED Node {node_id} | Stake: {self.S} | Reason: {reason}\n")

        return True
