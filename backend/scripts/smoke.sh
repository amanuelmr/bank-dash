#!/usr/bin/env bash
# End-to-end smoke test against a running API.
# Usage: ./scripts/smoke.sh [base-url]
set -uo pipefail

BASE="${1:-http://127.0.0.1:8000/api/v1}"
CURL=(curl -sS -m 10 --noproxy '*' -H 'Content-Type: application/json')

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
TOKEN=$(jq -r '.data.accessToken' <<<"$LOGIN")
REFRESH=$(jq -r '.data.refreshToken' <<<"$LOGIN")
check "login succeeds"      "true"    "$(jq -r '.success' <<<"$LOGIN")"
check "camelCase token key" "true"    "$(jq -r '.data | has("accessToken") and has("refreshToken")' <<<"$LOGIN")"
check "tokenType"           "Bearer"  "$(jq -r '.data.tokenType' <<<"$LOGIN")"
check "bad password 401"    "401"     "$("${CURL[@]}" -o /dev/null -w '%{http_code}' -X POST "$BASE/auth/login" -d '{"username":"tester","password":"nope"}')"
check "no token -> 401"     "401"     "$("${CURL[@]}" -o /dev/null -w '%{http_code}' "$BASE/users/me")"

section "refresh rotation"
R=$("${CURL[@]}" -X POST "$BASE/auth/refresh" -d "{\"refreshToken\":\"$REFRESH\"}")
NEW_REFRESH=$(jq -r '.data.refreshToken' <<<"$R")
check "token rotated"       "true"    "$([[ "$NEW_REFRESH" != "$REFRESH" ]] && echo true || echo false)"
check "old token rejected"  "401"     "$("${CURL[@]}" -o /dev/null -w '%{http_code}' -X POST "$BASE/auth/refresh" -d "{\"refreshToken\":\"$REFRESH\"}")"

A=(-H "Authorization: Bearer $TOKEN")

section "users"
ME=$("${CURL[@]}" "${A[@]}" "$BASE/users/me")
check "username"            "tester"  "$(jq -r '.data.username' <<<"$ME")"
check "role"                "ADMIN"   "$(jq -r '.data.role' <<<"$ME")"
check "preferences present" "true"    "$(jq -r '.data.preferences != null' <<<"$ME")"
check "no password leaked"  "true"    "$(jq -r '.data | has("password") or has("hashedPassword") | not' <<<"$ME")"
SUM=$("${CURL[@]}" "${A[@]}" "$BASE/users/me/summary")
check "summary keys"        "true"    "$(jq -r '.data | has("accountBalance") and has("totalIncome") and has("totalExpense") and has("totalSavings")' <<<"$SUM")"
check "balance positive"    "true"    "$(jq -r '.data.accountBalance > 0' <<<"$SUM")"
INV=$("${CURL[@]}" "${A[@]}" "$BASE/users/me/investment-summary?years=5&months=8")
check "5 yearly points"     "5"       "$(jq -r '.data.yearlyInvestments | length' <<<"$INV")"
check "8 monthly points"    "8"       "$(jq -r '.data.monthlyRevenue | length' <<<"$INV")"
check "numeric totals"      "true"    "$(jq -r '.data.totalInvestment | type == "number"' <<<"$INV")"

section "cards"
CARDS=$("${CURL[@]}" "${A[@]}" "$BASE/cards?page=0&size=10")
check "paged envelope"      "true"    "$(jq -r '.data | has("items") and has("totalItems") and has("totalPages")' <<<"$CARDS")"
check "has cards"           "true"    "$(jq -r '.data.totalItems > 0' <<<"$CARDS")"
check "numbers masked"      "true"    "$(jq -r 'all(.data.items[]; .maskedNumber | startswith("****"))' <<<"$CARDS")"
check "expiry is YYYY-MM-DD" "true"   "$(jq -r 'all(.data.items[]; .expiryDate | length == 10)' <<<"$CARDS")"

section "transactions"
TX=$("${CURL[@]}" "${A[@]}" "$BASE/transactions?page=0&size=5")
check "page fields"         "true"    "$(jq -r '.data | has("items") and has("page") and has("size") and has("hasNext") and has("hasPrevious")' <<<"$TX")"
check "page is 0-indexed"   "0"       "$(jq -r '.data.page' <<<"$TX")"
check "has history"         "true"    "$(jq -r '.data.totalItems > 0' <<<"$TX")"
check "UTC Z timestamps"    "true"    "$(jq -r 'all(.data.items[]; .occurredAt | endswith("Z"))' <<<"$TX")"
check "amounts positive"    "true"    "$(jq -r 'all(.data.items[]; .amount > 0)' <<<"$TX")"
check "camelCase sender"    "true"    "$(jq -r 'all(.data.items[]; has("senderUsername") and has("receiverUsername"))' <<<"$TX")"
INC=$("${CURL[@]}" "${A[@]}" "$BASE/transactions/incomes?page=0&size=3")
EXP=$("${CURL[@]}" "${A[@]}" "$BASE/transactions/expenses?page=0&size=3")
check "incomes are IN"      "true"    "$(jq -r 'all(.data.items[]; .direction == "IN")' <<<"$INC")"
check "expenses are OUT"    "true"    "$(jq -r 'all(.data.items[]; .direction == "OUT")' <<<"$EXP")"
BH=$("${CURL[@]}" "${A[@]}" "$BASE/transactions/balance-history?months=6")
check "6 points"            "6"       "$(jq -r '.data | length' <<<"$BH")"
check "period is YYYY-MM"   "true"    "$(jq -r 'all(.data[]; (.period | length) == 7 and (.period[4:5]) == "-")' <<<"$BH")"
check "last point = balance" "true"   "$(jq -r --argjson b "$(jq -c '.data.accountBalance' <<<"$ME")" '(.data[-1].value) as $v | ((($v - $b) | fabs) < 0.01)' <<<"$BH")"
REC=$("${CURL[@]}" "${A[@]}" "$BASE/transactions/transfer-recipients?limit=6")
check "recipients present"  "true"    "$(jq -r '.data | length > 0' <<<"$REC")"
check "never includes self" "true"    "$(jq -r '[.data[].username] | index("tester") == null' <<<"$REC")"

section "transfer writes both legs"
BEFORE=$(jq -r '.data.accountBalance' <<<"$ME")
T=$("${CURL[@]}" "${A[@]}" -X POST "$BASE/transactions" -d '{"type":"transfer","amount":25,"receiverUsername":"alice"}')
check "transfer created"    "true"    "$(jq -r '.success' <<<"$T")"
check "direction OUT"       "OUT"     "$(jq -r '.data.direction' <<<"$T")"
check "TXN id format"       "true"    "$(jq -r '.data.transactionId | startswith("TXN-")' <<<"$T")"
AFTER=$("${CURL[@]}" "${A[@]}" "$BASE/users/me" | jq -r '.data.accountBalance')
check "sender debited 25"   "true"    "$(jq -rn --argjson b "$BEFORE" --argjson a "$AFTER" '(($b - $a) == 25)')"
POOR=$("${CURL[@]}" "${A[@]}" -X POST "$BASE/transactions" -d '{"type":"transfer","amount":99999999,"receiverUsername":"alice"}')
check "overdraft blocked"   "true"    "$(jq -r '.data.code == "insufficient_funds"' <<<"$POOR")"

section "loans"
LOANS=$("${CURL[@]}" "${A[@]}" "$BASE/loans?page=0&size=5")
check "loans paged"         "true"    "$(jq -r '.data.totalItems > 0' <<<"$LOANS")"
check "loan fields"         "true"    "$(jq -r '.data.items[0] | has("loanAmount") and has("amountLeftToRepay") and has("installment") and has("interestRate") and has("loanDuration")' <<<"$LOANS")"
LS=$("${CURL[@]}" "${A[@]}" "$BASE/loans/summary")
check "summary by type"     "true"    "$(jq -r '.data | has("personalLoan") and has("corporateLoan") and has("businessLoan") and has("totalOutstanding")' <<<"$LS")"

section "catalogue"
SVC=$("${CURL[@]}" "${A[@]}" "$BASE/bank-services?page=0&size=5")
check "services listed"     "true"    "$(jq -r '.data.totalItems > 0' <<<"$SVC")"
SEARCH=$("${CURL[@]}" "${A[@]}" "$BASE/bank-services/search?q=savings")
check "search returns hits" "true"    "$(jq -r '.data | length > 0' <<<"$SEARCH")"
TREND=$("${CURL[@]}" "${A[@]}" "$BASE/companies/trending?limit=4")
check "only trending"       "true"    "$(jq -r 'all(.data[]; .isTrending)' <<<"$TREND")"
check "ranked by change"    "true"    "$(jq -r '[.data[].changePercent] as $p | ($p == ($p | sort | reverse))' <<<"$TREND")"

section "error envelope"
E=$("${CURL[@]}" "${A[@]}" "$BASE/loans/not-a-real-id")
check "404 uses envelope"   "true"    "$(jq -r '.success == false and (.message | length > 0) and (.data.code == "not_found")' <<<"$E")"
V=$("${CURL[@]}" "${A[@]}" -X POST "$BASE/cards" -d '{"cardType":"X","cardHolder":"Y","expiryDate":"2030-01-01","passcode":"1"}')
check "422 uses envelope"   "true"    "$(jq -r '.data.code == "validation_error"' <<<"$V")"
check "422 http status"     "422"     "$("${CURL[@]}" "${A[@]}" -o /dev/null -w '%{http_code}' -X POST "$BASE/cards" -d '{"cardType":"X"}')"

printf '\n\033[1m%d passed, %d failed\033[0m\n' "$pass" "$fail"
[[ $fail -eq 0 ]]