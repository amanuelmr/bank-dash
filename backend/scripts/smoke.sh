#!/usr/bin/env bash
# End-to-end smoke test against a running API.
# Usage: ./scripts/smoke.sh [base-url]
set -uo pipefail

BASE="${1:-http://127.0.0.1:8000/api/v1}"
# Auth is cookie based, so drive the script the way a browser does: a real
# cookie jar. See the bearer check near the end for the CLI path.
JAR="$(mktemp -t bankdash-smoke.XXXXXX)"
trap 'rm -f "$JAR"' EXIT
CURL=(curl -sS -m 10 --noproxy '*' -c "$JAR" -b "$JAR" -H 'Content-Type: application/json')

pass=0
fail=0
check() { # check <label> <expected> <actual>
  if [[ "$3" == "$2" ]]; then
    printf '  \033[32mPASS\033[0m %-44s %s\n' "$1" "$3"; ((pass++))
  else
    printf '  \033[31mFAIL\033[0m %-44s expected %q, got %q\n' "$1" "$2" "$3"; ((fail++))
  fi
}
section() { printf '\n\033[1m%s\033[0m\n' "$1"; }

section "health"
H=$("${CURL[@]}" "$BASE/health")
check "success flag"        "true"    "$(jq -r '.success' <<<"$H")"
check "database up"         "up"      "$(jq -r '.data.database' <<<"$H")"

section "auth"
LOGIN=$("${CURL[@]}" -X POST "$BASE/auth/login" -d '{"username":"tester","password":"12345678"}')
check "login succeeds"      "true"    "$(jq -r '.success' <<<"$LOGIN")"
check "login returns user"  "tester"  "$(jq -r '.data.username' <<<"$LOGIN")"
check "no token in body"    "true"    "$(jq -r '.data | has("accessToken") | not' <<<"$LOGIN")"
check "bad password 401"    "401"     "$("${CURL[@]}" -o /dev/null -w '%{http_code}' -X POST "$BASE/auth/login" -d '{"username":"tester","password":"nope"}')"
# Deliberately bypasses the cookie jar: this asserts that an unauthenticated
# caller is rejected.
check "no credentials -> 401" "401" \
  "$(curl -sS -m 10 --noproxy '*' -o /dev/null -w '%{http_code}' "$BASE/users/me")"

section "session"
check "refresh with no body"  "200"   "$("${CURL[@]}" -o /dev/null -w '%{http_code}' -X POST "$BASE/auth/refresh")"
check "still authenticated"   "200"   "$("${CURL[@]}" -o /dev/null -w '%{http_code}' "$BASE/users/me")"
check "auth cookies are httponly" "true" \
  "$(curl -sS -m 10 --noproxy '*' -o /dev/null -D - -X POST "$BASE/auth/login" \
      -H 'Content-Type: application/json' -d '{"username":"tester","password":"12345678"}' \
     | grep -ci 'set-cookie:.*httponly' | awk '{print ($1 >= 2) ? "true" : "false"}')"

# Deliberately cookie-less: an httpOnly cookie can only be expired by the server,
# so a rejected refresh has to clear them. Otherwise the dead cookie rides along
# for its full 30-day lifetime and every call pays a doomed refresh first.
COOKIE_DUMP=$(curl -sS -m 10 --noproxy '*' -o /dev/null -D - -X POST "$BASE/auth/refresh")
check "failed refresh -> 401"  "401" "$(awk '/^HTTP/{print $2}' <<<"$COOKIE_DUMP" | tail -1)"
check "failed refresh clears both cookies" "true" \
  "$(grep -ci 'set-cookie:.*Max-Age=0' <<<"$COOKIE_DUMP" | awk '{print ($1 == 2) ? "true" : "false"}')"

# The refresh token is only ever presented to /auth/*, so it is scoped there
# rather than riding along with every API call.
LOGIN_DUMP=$(curl -sS -m 10 --noproxy '*' -o /dev/null -D - -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' -d '{"username":"tester","password":"12345678"}')
check "access cookie path"  "Path=/"            "$(grep -i 'set-cookie: accessToken='  <<<"$LOGIN_DUMP" | grep -oi 'Path=[^;]*' | tr -d '\r')"
check "refresh cookie path" "Path=/api/v1/auth" "$(grep -i 'set-cookie: refreshToken=' <<<"$LOGIN_DUMP" | grep -oi 'Path=[^;]*' | tr -d '\r')"

# The access cookie must outlive the 24h JWT it carries. The refresh cookie is
# scoped to the API and never reaches the frontend's route gate, so if this
# cookie died on the token's schedule the gate would sign everyone out while
# their refresh token still had weeks left.
# An access token cannot be revoked before it expires, so this is how long a
# leak stays usable. Decoded from the issued token rather than read from config,
# so it verifies what is actually handed out.
TTL=$(grep -i 'set-cookie: accessToken=' <<<"$LOGIN_DUMP" \
  | sed 's/.*accessToken=\([^;]*\).*/\1/' | tr -d '\r' \
  | cut -d. -f2 | tr '_-' '/+' | awk '{l=length($0)%4; if(l==2)$0=$0"=="; else if(l==3)$0=$0"="; print}' \
  | base64 -d 2>/dev/null | jq -r '.exp - .iat')
check "access token short-lived" "true" \
  "$(awk -v t="$TTL" 'BEGIN{print (t > 0 && t <= 3600) ? "true" : "false"}')"
check "access cookie outlives its JWT" "true" \
  "$(grep -i 'set-cookie: accessToken=' <<<"$LOGIN_DUMP" | grep -oi 'Max-Age=[0-9]*' | cut -d= -f2 \
     | awk '{print ($1 > 86400) ? "true" : "false"}')"

section "bearer path (non-browser clients)"
BEARER=$(curl -sS -m 10 --noproxy '*' -D - -o /dev/null -X POST "$BASE/auth/login" \
  -H 'Content-Type: application/json' -d '{"username":"tester","password":"12345678"}' \
  | grep -i '^set-cookie: accessToken=' | sed 's/.*accessToken=\([^;]*\).*/\1/' | tr -d '\r')
check "bearer token obtainable" "true" "$([[ -n "$BEARER" ]] && echo true || echo false)"
check "bearer accepted"         "200"   "$(curl -sS -m 10 --noproxy '*' -o /dev/null -w '%{http_code}' -H "Authorization: Bearer $BEARER" "$BASE/users/me")"
section "users"
ME=$("${CURL[@]}" "$BASE/users/me")
check "username"            "tester"  "$(jq -r '.data.username' <<<"$ME")"
check "role"                "ADMIN"   "$(jq -r '.data.role' <<<"$ME")"
check "preferences present" "true"    "$(jq -r '.data.preferences != null' <<<"$ME")"
check "no password leaked"  "true"    "$(jq -r '.data | has("password") or has("hashedPassword") | not' <<<"$ME")"
SUM=$("${CURL[@]}" "$BASE/users/me/summary")
check "summary keys"        "true"    "$(jq -r '.data | has("accountBalance") and has("totalIncome") and has("totalExpense") and has("totalSavings")' <<<"$SUM")"
check "balance positive"    "true"    "$(jq -r '.data.accountBalance > 0' <<<"$SUM")"
INV=$("${CURL[@]}" "$BASE/users/me/investment-summary?years=5&months=8")
check "5 yearly points"     "5"       "$(jq -r '.data.yearlyInvestments | length' <<<"$INV")"
check "8 monthly points"    "8"       "$(jq -r '.data.monthlyRevenue | length' <<<"$INV")"
check "numeric totals"      "true"    "$(jq -r '.data.totalInvestment | type == "number"' <<<"$INV")"

section "cards"
CARDS=$("${CURL[@]}" "$BASE/cards?page=0&size=10")
check "paged envelope"      "true"    "$(jq -r '.data | has("items") and has("totalItems") and has("totalPages")' <<<"$CARDS")"
check "has cards"           "true"    "$(jq -r '.data.totalItems > 0' <<<"$CARDS")"
check "numbers masked"      "true"    "$(jq -r 'all(.data.items[]; .maskedNumber | startswith("****"))' <<<"$CARDS")"
check "expiry is YYYY-MM-DD" "true"   "$(jq -r 'all(.data.items[]; .expiryDate | length == 10)' <<<"$CARDS")"

section "transactions"
TX=$("${CURL[@]}" "$BASE/transactions?page=0&size=5")
check "page fields"         "true"    "$(jq -r '.data | has("items") and has("page") and has("size") and has("hasNext") and has("hasPrevious")' <<<"$TX")"
check "page is 0-indexed"   "0"       "$(jq -r '.data.page' <<<"$TX")"
check "has history"         "true"    "$(jq -r '.data.totalItems > 0' <<<"$TX")"
check "UTC Z timestamps"    "true"    "$(jq -r 'all(.data.items[]; .occurredAt | endswith("Z"))' <<<"$TX")"
check "amounts positive"    "true"    "$(jq -r 'all(.data.items[]; .amount > 0)' <<<"$TX")"
check "camelCase sender"    "true"    "$(jq -r 'all(.data.items[]; has("senderUsername") and has("receiverUsername"))' <<<"$TX")"
INC=$("${CURL[@]}" "$BASE/transactions/incomes?page=0&size=3")
EXP=$("${CURL[@]}" "$BASE/transactions/expenses?page=0&size=3")
check "incomes are IN"      "true"    "$(jq -r 'all(.data.items[]; .direction == "IN")' <<<"$INC")"
check "expenses are OUT"    "true"    "$(jq -r 'all(.data.items[]; .direction == "OUT")' <<<"$EXP")"
BH=$("${CURL[@]}" "$BASE/transactions/balance-history?months=6")
check "6 points"            "6"       "$(jq -r '.data | length' <<<"$BH")"
check "period is YYYY-MM"   "true"    "$(jq -r 'all(.data[]; (.period | length) == 7 and (.period[4:5]) == "-")' <<<"$BH")"
check "last point = balance" "true"   "$(jq -r --argjson b "$(jq -c '.data.accountBalance' <<<"$ME")" '(.data[-1].value) as $v | ((($v - $b) | fabs) < 0.01)' <<<"$BH")"
REC=$("${CURL[@]}" "$BASE/transactions/transfer-recipients?limit=6")
check "recipients present"  "true"    "$(jq -r '.data | length > 0' <<<"$REC")"
check "never includes self" "true"    "$(jq -r '[.data[].username] | index("tester") == null' <<<"$REC")"

section "transfer writes both legs"
BEFORE=$(jq -r '.data.accountBalance' <<<"$ME")
T=$("${CURL[@]}" -X POST "$BASE/transactions" -d '{"type":"transfer","amount":25,"receiverUsername":"alice"}')
check "transfer created"    "true"    "$(jq -r '.success' <<<"$T")"
check "direction OUT"       "OUT"     "$(jq -r '.data.direction' <<<"$T")"
check "TXN id format"       "true"    "$(jq -r '.data.transactionId | startswith("TXN-")' <<<"$T")"
AFTER=$("${CURL[@]}" "$BASE/users/me" | jq -r '.data.accountBalance')
check "sender debited 25"   "true"    "$(jq -rn --argjson b "$BEFORE" --argjson a "$AFTER" '(($b - $a) == 25)')"
POOR=$("${CURL[@]}" -X POST "$BASE/transactions" -d '{"type":"transfer","amount":99999999,"receiverUsername":"alice"}')
check "overdraft blocked"   "true"    "$(jq -r '.data.code == "insufficient_funds"' <<<"$POOR")"

section "loans"
LOANS=$("${CURL[@]}" "$BASE/loans?page=0&size=5")
check "loans paged"         "true"    "$(jq -r '.data.totalItems > 0' <<<"$LOANS")"
check "loan fields"         "true"    "$(jq -r '.data.items[0] | has("loanAmount") and has("amountLeftToRepay") and has("installment") and has("interestRate") and has("loanDuration")' <<<"$LOANS")"
LS=$("${CURL[@]}" "$BASE/loans/summary")
check "summary by type"     "true"    "$(jq -r '.data | has("personalLoan") and has("corporateLoan") and has("businessLoan") and has("totalOutstanding")' <<<"$LS")"

section "catalogue"
SVC=$("${CURL[@]}" "$BASE/bank-services?page=0&size=5")
check "services listed"     "true"    "$(jq -r '.data.totalItems > 0' <<<"$SVC")"
SEARCH=$("${CURL[@]}" "$BASE/bank-services/search?q=savings")
check "search returns hits" "true"    "$(jq -r '.data | length > 0' <<<"$SEARCH")"
TREND=$("${CURL[@]}" "$BASE/companies/trending?limit=4")
check "only trending"       "true"    "$(jq -r 'all(.data[]; .isTrending)' <<<"$TREND")"
check "ranked by change"    "true"    "$(jq -r '[.data[].changePercent] as $p | ($p == ($p | sort | reverse))' <<<"$TREND")"

section "error envelope"
E=$("${CURL[@]}" "$BASE/loans/not-a-real-id")
check "404 uses envelope"   "true"    "$(jq -r '.success == false and (.message | length > 0) and (.data.code == "not_found")' <<<"$E")"
V=$("${CURL[@]}" -X POST "$BASE/cards" -d '{"cardType":"X","cardHolder":"Y","expiryDate":"2030-01-01","passcode":"1"}')
check "422 uses envelope"   "true"    "$(jq -r '.data.code == "validation_error"' <<<"$V")"
check "422 http status"     "422"     "$("${CURL[@]}" -o /dev/null -w '%{http_code}' -X POST "$BASE/cards" -d '{"cardType":"X"}')"

printf '\n\033[1m%d passed, %d failed\033[0m\n' "$pass" "$fail"
[[ $fail -eq 0 ]]
