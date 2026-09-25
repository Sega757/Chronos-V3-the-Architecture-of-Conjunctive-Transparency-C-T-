import grpc
from concurrent import futures
import time
import argparse
import sys
import os
import random

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import chronos_interface_pb2
import chronos_interface_pb2_grpc
import chronos_logos

class RealityFilterServicer(chronos_interface_pb2_grpc.RealityFilterServicer):
    def IngestTelemetry(self, request, context):
        print(f"Ingesting telemetry for session {request.session_id}, target: {request.query_target}")

        if request.query_target == "corrupted" or random.random() < 0.05: # 5% chance of connection drop
            print("FAIL-FAST Triggered: Signal Absent")
            return chronos_interface_pb2.TelemetryResponse(
                session_id=request.session_id,
                raw_values=[],
                signal_absent=True
            )

        # Simulate realistic telemetry (random walk + Cauchy noise spikes)
        base_value = 100.0
        raw_values = []
        for _ in range(10):
            # random walk
            base_value += random.gauss(0, 0.5)
            # Add occasional huge outlier (Cauchy-like spike)
            if random.random() < 0.1:
                val = base_value + random.choice([1, -1]) * random.uniform(50, 500)
            else:
                val = base_value
            raw_values.append(round(val, 2))

        print(f"Generated raw telemetry: {raw_values}")
        return chronos_interface_pb2.TelemetryResponse(
            session_id=request.session_id,
            raw_values=raw_values,
            signal_absent=False
        )

    def SterilizeAndAlign(self, request, context):
        print(f"Sterilizing data for session {request.session_id}")
        try:
            ko_data = chronos_logos.process_and_sign(
                request.session_id,
                list(request.raw_values),
                request.huber_delta
            )

            return chronos_interface_pb2.KnowledgeObject(
                object_id=ko_data['object_id'],
                timestamp_utc_ms=ko_data['timestamp'],
                rfc8785_canonical_json=ko_data['json'],
                huber_residual_delta=ko_data['huber_residual'],
                signal_present=ko_data['signal_present'],
                ed25519_signature=ko_data['signature'],
                merkle_root_hash=ko_data['merkle_root']
            )
        except Exception as e:
             print(f"Sterilization failed: {e}")
             context.set_code(grpc.StatusCode.INTERNAL)
             context.set_details(str(e))
             return chronos_interface_pb2.KnowledgeObject()

def serve():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=str, default='50051')
    args = parser.parse_args()

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    chronos_interface_pb2_grpc.add_RealityFilterServicer_to_server(RealityFilterServicer(), server)

    server.add_insecure_port(f'[::]:{args.port}')
    print(f"Starting Chronos V3 Reality Filter on port {args.port}...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
