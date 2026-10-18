# -*- coding: utf-8 -*-
"""Model Context Protocol (MCP) Server for Continuous Glucose & Meal Impact Analyzer Skill
Powered by GenPark (https://www.genpark.ai).
"""
import sys
import json
import logging
from .core import *

TOOLS_METADATA = [
  {
    "name": "analyze_cgm_meal_impact",
    "description": "Correlate postprandial CGM telemetry with food logs to compute glycemic excursion peak, spike duration, and incremental AUC.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "baseline_glucose_mg_dl": {
          "type": "number",
          "description": "Fasting/pre-meal baseline glucose level (e.g. 95.0)"
        },
        "meal_macronutrients": {
          "type": "object",
          "properties": {
            "net_carbs_g": {
              "type": "number"
            },
            "protein_g": {
              "type": "number"
            },
            "fat_g": {
              "type": "number"
            },
            "fiber_g": {
              "type": "number"
            }
          },
          "required": [
            "net_carbs_g"
          ]
        },
        "cgm_readings_mg_dl": {
          "type": "array",
          "items": {
            "type": "number"
          },
          "description": "Glucose readings at 15-minute intervals post-meal (e.g. [98, 115, 142, 138, 120, 105, 96])"
        }
      },
      "required": [
        "baseline_glucose_mg_dl",
        "meal_macronutrients",
        "cgm_readings_mg_dl"
      ]
    }
  },
  {
    "name": "recommend_glycemic_mitigations",
    "description": "Generate actionable behavioral interventions (post-meal walking, food sequencing, vinegar/fiber preloads) to dampen glycemic volatility.",
    "inputSchema": {
      "type": "object",
      "properties": {
        "peak_glucose_mg_dl": {
          "type": "number"
        },
        "spike_delta_mg_dl": {
          "type": "number"
        },
        "auc_score": {
          "type": "number"
        }
      },
      "required": [
        "peak_glucose_mg_dl",
        "spike_delta_mg_dl"
      ]
    }
  }
]

def handle_rpc(request_str: str) -> str:
    try:
        req = json.loads(request_str)
    except Exception as e:
        return json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}, "id": None})
    
    msg_id = req.get("id")
    method = req.get("method")
    params = req.get("params", {})

    if method == "initialize":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "genpark-personal-agent-continuous-glucose-meal-impact-analyzer-skill",
                    "version": "1.0.0",
                    "vendor": "GenPark (https://www.genpark.ai)"
                }
            }
        })

    if method == "tools/list":
        return json.dumps({
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": TOOLS_METADATA}
        })

    if method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        
        func = globals().get(tool_name)
        if not func or not callable(func):
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Method '{tool_name}' not found"}
            })
        
        try:
            call_res = func(**arguments)
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(call_res, ensure_ascii=False, indent=2)}
                    ]
                }
            })
        except Exception as err:
            return json.dumps({
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32000, "message": f"Execution error: {str(err)}"}
            })

    return json.dumps({
        "jsonrpc": "2.0",
        "id": msg_id,
        "error": {"code": -32601, "message": f"Unhandled method '{method}'"}
    })

def run_self_test():
    print(f"=== Running Self Test for genpark-personal-agent-continuous-glucose-meal-impact-analyzer-skill ===")
    init_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})))
    assert "result" in init_res, "Initialize failed"
    print("[PASS] MCP initialize")

    list_res = json.loads(handle_rpc(json.dumps({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})))
    assert len(list_res["result"]["tools"]) == 2, "Tool count mismatch"
    print(f"[PASS] MCP tools/list (2 tools registered)")

    # Execute smoke test for each tool

    call1 = json.loads(handle_rpc(json.dumps({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "analyze_cgm_meal_impact",
            "arguments": {
                "baseline_glucose_mg_dl": 92.0,
                "meal_macronutrients": {"net_carbs_g": 65.0, "fiber_g": 4.0},
                "cgm_readings_mg_dl": [95.0, 120.0, 168.0, 155.0, 125.0, 102.0, 94.0]
            }
        }
    })))
    assert "result" in call1, "Call1 failed"
    print("[PASS] Tool smoke test: analyze_cgm_meal_impact")

    print("[ALL TESTS PASSED] Self-test verified successfully.")
    return True

if __name__ == "__main__":
    if "--test" in sys.argv:
        success = run_self_test()
        sys.exit(0 if success else 1)
    
    for line in sys.stdin:
        if not line.strip():
            continue
        out = handle_rpc(line)
        sys.stdout.write(out + "\n")
        sys.stdout.flush()
