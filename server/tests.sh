#!/usr/bin/env bash

set -Eeu pipefail

# Approov authentication check
approov api -list
if [ $? -ne 0 ]; then
  echo "Approov authentication failed. Tests will not run."
  exit 1
fi

# ---------- config ----------
BASE_URL="${BASE_URL:-http://localhost:8080}"
TOKDIR="${TOKDIR:-.config}"


# Check Approov state before running tests
echo "Checking Approov state..."
state_resp=$(curl -i -s "$BASE_URL/approov-state")
state_code=$(echo "$state_resp" | grep -m1 HTTP | awk '{print $2}')
state_body=$(echo "$state_resp" | sed '1,/^$/d')
echo "Approov state HTTP code: $state_code"
echo "Approov state body: $state_body"
echo

# Set approov_disabled variable
if [ "$state_code" = "501" ]; then
  approov_disabled=true
else
  approov_disabled=false
fi

HDR_NAME="approov-token" 




LOGDIR="$TOKDIR/logs"
mkdir -p "$TOKDIR"
mkdir -p "$LOGDIR"

# Create a log file with date and time
LOGFILE="$LOGDIR/$(date '+%Y-%m-%d_%H-%M-%S').log"


need_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "${red}Missing command: $1${reset}"
    exit 1
  }
}


need_cmd approov
need_cmd curl


# Helper to run curl and print concise result

# Helper to run curl, check status, and print concise result

run_test() {
  local name="$1"; shift
  local expected="$1"; shift
  local resp status
  resp=$(curl -i -s "$@")
  status=$(echo "$resp" | grep -m1 HTTP | awk '{print $2}')
  local result
  if [ "$status" = "$expected" ]; then
    result="Passed"
  else
    result="Failed"
  fi
  echo "$name: $result"
  test_results+=("$name: $result")
  {
    echo "===== $name ====="
    echo "$resp"
    if [ "$approov_disabled" = true ]; then
      echo "Approov State: disabled, no checks performed."
    else
      echo "Approov State: enabled, token checks performed."
    fi
    echo
  } >> "$LOGFILE" 2>&1
}



# 0 Unprotected endpoint
expected_status=200
run_test "Unprotected" "$expected_status" "$BASE_URL/unprotected"

# 1 Protected endpoint

# 1.1 Valid Token
approov token -genExample example.com > "$TOKDIR/approov_token_1_valid"
if [ "$approov_disabled" = true ]; then expected_status=200; else expected_status=200; fi
run_test "Token check (valid)" "$expected_status" -H "approov-token: $(cat "$TOKDIR/approov_token_1_valid")" "$BASE_URL/token-check"

# 1.2 Invalid Token 
approov token -genExample example.com -type invalid > "$TOKDIR/approov_token_1_invalid"
if [ "$approov_disabled" = true ]; then expected_status=200; else expected_status=401; fi
run_test "Token check (invalid)" "$expected_status" -H "approov-token: $(cat "$TOKDIR/approov_token_1_invalid")" "$BASE_URL/token-check"

# 2 Token Binding ["Authorization"]
AUTH_VAL="ExampleAuthToken=="
export HASH_INPUT="$AUTH_VAL"

# 2.1 Valid Token
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com > "$TOKDIR/approov_token_2_valid"
if [ "$approov_disabled" = true ]; then expected_status=200; else expected_status=200; fi
run_test "Token Binding (valid)" "$expected_status" -H "Authorization: $AUTH_VAL" -H "approov-token: $(cat "$TOKDIR/approov_token_2_valid")" "$BASE_URL/token-binding-1"

# 2.2 Missing Header
if [ "$approov_disabled" = true ]; then expected_status=200; else expected_status=401; fi
run_test "Token Binding (missing header)" "$expected_status" -H "approov-token: $(cat "$TOKDIR/approov_token_2_valid")" "$BASE_URL/token-binding-1"

# 2.3 Incorrect Header
if [ "$approov_disabled" = true ]; then expected_status=200; else expected_status=401; fi
run_test "Token Binding (incorrect header)" "$expected_status" -H "Authorization: BadAuthToken==" -H "approov-token: $(cat "$TOKDIR/approov_token_2_valid")" "$BASE_URL/token-binding-1"

# 2.4 Invalid Token
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com -type invalid > "$TOKDIR/approov_token_2_invalid"
if [ "$approov_disabled" = true ]; then expected_status=200; else expected_status=401; fi
run_test "Token Binding (invalid token)" "$expected_status" -H "Authorization: $AUTH_VAL" -H "approov-token: $(cat "$TOKDIR/approov_token_2_invalid")" "$BASE_URL/token-binding-1"

# 3 Token Binding ["Authorization", "Content-Digest"]
AUTH_VAL2="ExampleAuthToken=="
CD_VAL="ContentDigest=="
export HASH_INPUT="${AUTH_VAL2}${CD_VAL}"

# 3.1 Valid Token
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com > "$TOKDIR/approov_token_3_valid"
if [ "$approov_disabled" = true ]; then expected_status=200; else expected_status=200; fi
run_test "Token Binding 2 (valid)" "$expected_status" -H "Authorization: $AUTH_VAL2" -H "Content-Digest: $CD_VAL" -H "approov-token: $(cat "$TOKDIR/approov_token_3_valid")" "$BASE_URL/token-binding-2"

# 3.2 Missing header
if [ "$approov_disabled" = true ]; then expected_status=200; else expected_status=401; fi
run_test "Token Binding 2 (missing header)" "$expected_status" -H "approov-token: $(cat "$TOKDIR/approov_token_3_valid")" "$BASE_URL/token-binding-2"

# 3.3 Incorrect Header
if [ "$approov_disabled" = true ]; then expected_status=200; else expected_status=401; fi
run_test "Token Binding 2 (incorrect header)" "$expected_status" -H "Authorization: BadAuthToken==" -H "Content-Digest: BadContentDigest==" -H "approov-token: $(cat "$TOKDIR/approov_token_3_valid")" "$BASE_URL/token-binding-2"

# 3.4 Invalid Token
approov token -setDataHashInToken "$HASH_INPUT" -genExample example.com -type invalid > "$TOKDIR/approov_token_3_invalid"
if [ "$approov_disabled" = true ]; then expected_status=200; else expected_status=401; fi
run_test "Token Binding 2 (invalid token)" "$expected_status" -H "Authorization: $AUTH_VAL2" -H "Content-Digest: $CD_VAL" -H "approov-token: $(cat "$TOKDIR/approov_token_3_invalid")" "$BASE_URL/token-binding-2"

# Print summary of all test results
echo
echo "Full request and response details are saved in: $LOGFILE"
