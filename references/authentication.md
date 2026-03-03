# Authentication Reference

This file gives you a deterministic procedure for discovering what authencation an
operation requires and building the correct curl flags. Authentication errors are the
most common failure mode when calling APIs — follow this sequence exactly.

---

## Lookup Sequence

1. **Check operation-level security** — highest priority:
   ```bash
   jaq --arg path "PATH" --arg method "METHOD" \
     '.paths[$path][$method].security' spec.json
   ```

2. **If null, fall back to global security** — applies to all operations:
   ```bash
   jaq '.security // []' spec.json
   ```

3. **If still empty (`[]`) — no auth required** for this operation.
   Proceed without auth headers (see [No Auth](#no-auth)).

4. **Look up scheme definition** in `components.securitySchemes`:
   ```bash
   jaq --arg name "SCHEME_NAME" '.components.securitySchemes[$name]' spec.json
   ```

5. **List all available scheme names** (to know what names appear in step 1 output):
   ```bash
   jaq '[.components.securitySchemes // {} | keys[]]' spec.json
   ```

**Combined lookup — effective security for one operation:**
```bash
jaq --arg path "PATH" --arg method "METHOD" \
  '.paths[$path][$method].security // .security // []' spec.json
```

---

## Scheme: `apiKey` (header)

**Detection:**
```json
{"type": "apiKey", "name": "api_key", "in": "header"}
```

**curl flag:**
```bash
curl -H "$NAME: $VALUE" ...
# Example: -H "api_key: my-api-key-value"
```

The header name is the `name` field from the scheme definition — it is **not** always
`Authorization`.

**Example — Petstore `api_key`:**
```bash
jaq --arg name "api_key" '.components.securitySchemes[$name]' examples/petstore/petstore.json
# → {"type": "apiKey", "name": "api_key", "in": "header"}
curl -H "api_key: $API_KEY" https://petstore3.swagger.io/api/v3/pet/1
```

**Missing credentials interrupt:**
> "This endpoint requires an API key in the `api_key` header.
> Please provide the API key value and I will include it in the request."

---

## Scheme: `apiKey` (query parameter)

**Detection:**
```json
{"type": "apiKey", "name": "api_key", "in": "query"}
```

**curl flag:** append as query parameter
```bash
curl "https://api.example.com/endpoint?$NAME=$VALUE" ...
# Example: curl "https://api.example.com/data?api_key=my-key"
```

**Missing credentials interrupt:**
> "This endpoint requires an API key as the `$NAME` query parameter.
> Please provide the key value."

---

## Scheme: `http/bearer`

**Detection:**
```json
{"type": "http", "scheme": "bearer"}
```

**curl flag:**
```bash
curl -H "Authorization: Bearer $TOKEN" ...
```

**Example — Stripe `bearerAuth`:**
```bash
jaq --arg name "bearerAuth" '.components.securitySchemes[$name]' examples/stripe/stripe-subset.json
# → {"type":"http","scheme":"bearer","description":"..."}
curl -H "Authorization: Bearer $STRIPE_SECRET_KEY" https://api.stripe.com/v1/customers/cus_123
```

**Missing credentials interrupt:**
> "This endpoint requires a Bearer token in the Authorization header.
> Please provide the token (e.g. a JWT or API secret) and I will include it."

---

## Scheme: `http/basic`

**Detection:**
```json
{"type": "http", "scheme": "basic"}
```

**curl flag:**
```bash
curl -u "$USERNAME:$PASSWORD" ...
# Or equivalently:
curl -H "Authorization: Basic $(printf '%s:%s' "$USERNAME" "$PASSWORD" | base64)" ...
```

**Example — Stripe `basicAuth`** (Stripe uses API key as username, empty password):
```bash
jaq --arg name "basicAuth" '.components.securitySchemes[$name]' examples/stripe/stripe-subset.json
# → {"type":"http","scheme":"basic","description":"Basic HTTP authentication..."}
curl -u "$STRIPE_SECRET_KEY:" https://api.stripe.com/v1/customers
# Note the trailing ":" — empty password field
```

**Missing credentials interrupt:**
> "This endpoint uses HTTP Basic authentication.
> Please provide the username and password (or API key for the username field)."

---

## Scheme: `oauth2`

**Detection:**
```json
{"type": "oauth2", "flows": {...}}
```

OAuth2 has four possible flows. Extract flow details:
```bash
jaq --arg name "SCHEME_NAME" '.components.securitySchemes[$name].flows | keys' spec.json
```

### Implicit flow

```json
{"implicit": {"authorizationUrl": "...", "scopes": {...}}}
```

The user must obtain a token via a browser redirect. Provide the `authorizationUrl`:
> "This operation uses OAuth2 implicit flow. The user needs to authorize at:
> `$AUTHORIZATION_URL`
> Please provide the resulting access token."

### Client Credentials flow

```json
{"clientCredentials": {"tokenUrl": "...", "scopes": {...}}}
```

```bash
# Get token
TOKEN=$(curl -s -X POST "$TOKEN_URL" \
  -d "grant_type=client_credentials&client_id=$CLIENT_ID&client_secret=$CLIENT_SECRET" \
  | jaq -r '.access_token')
# Use token
curl -H "Authorization: Bearer $TOKEN" ...
```

### Authorization Code flow

```json
{"authorizationCode": {"authorizationUrl": "...", "tokenUrl": "...", "scopes": {...}}}
```

Full OAuth2 code flow; requires browser redirect. Ask the user to authorize and provide
the resulting access token. Then use as Bearer.

### Password flow (deprecated)

```json
{"password": {"tokenUrl": "...", "scopes": {...}}}
```

```bash
TOKEN=$(curl -s -X POST "$TOKEN_URL" \
  -d "grant_type=password&username=$USER&password=$PASS&client_id=$CLIENT_ID" \
  | jaq -r '.access_token')
curl -H "Authorization: Bearer $TOKEN" ...
```

**Example — Petstore `petstore_auth` (implicit):**
```bash
jaq --arg name "petstore_auth" '.components.securitySchemes[$name]' examples/petstore/petstore.json
# → {"type":"oauth2","flows":{"implicit":{"authorizationUrl":"https://petstore3.swagger.io/oauth/authorize","scopes":{...}}}}
```
Required scopes for an operation are listed in the security array:
```json
[{"petstore_auth": ["write:pets", "read:pets"]}]
```
→ Token must include scopes `write:pets` and `read:pets`.

---

## Scheme: `openIdConnect`

**Detection:**
```json
{"type": "openIdConnect", "openIdConnectUrl": "..."}
```

Fetch the discovery document to find the token endpoint:
```bash
curl "$OPENID_CONNECT_URL" | jaq '{token_endpoint: .token_endpoint, authorization_endpoint: .authorization_endpoint}'
```

Then use the token as Bearer:
```bash
curl -H "Authorization: Bearer $TOKEN" ...
```

---

## No Auth

If the operation's `security` field is an empty array `[]` **or** absent with no global
security, proceed without auth headers:

```bash
curl https://api.example.com/public-endpoint
```

> **Note:** Empty `auth_schemes` from L0 does not guarantee all endpoints are public.
> GitHub, for example, has unauthenticated rate limits — some operations work without auth
> but return fewer results or are rate-limited. Always check the specific operation.

---

## Multiple Schemes (OR Logic)

When `security` lists multiple schemes, they are alternatives — pick one:
```json
[
  {"api_key": []},
  {"petstore_auth": ["write:pets", "read:pets"]}
]
```
→ Use `api_key` **or** `petstore_auth` — whichever credential you have.

Prefer `apiKey` schemes over `oauth2` when both are available (simpler to use).

---

## Quick Reference

| Scheme definition | curl construction |
|-------------------|-------------------|
| `{"type":"apiKey","name":"X","in":"header"}` | `-H "X: $VALUE"` |
| `{"type":"apiKey","name":"X","in":"query"}` | `?X=$VALUE` in URL |
| `{"type":"http","scheme":"bearer"}` | `-H "Authorization: Bearer $TOKEN"` |
| `{"type":"http","scheme":"basic"}` | `-u "$USER:$PASS"` |
| `{"type":"oauth2","flows":{"clientCredentials":...}}` | get token → Bearer |
| `{"type":"oauth2","flows":{"implicit":...}}` | browser redirect → Bearer |
| No security / empty `[]` | no auth headers |

---

## Regression Reference

| Spec | Command | Expected output |
|------|---------|-----------------|
| `examples/petstore/petstore.json` | `jaq '[.components.securitySchemes \| keys[]]'` | `["api_key","petstore_auth"]` |
| `examples/petstore/petstore.json` | `jaq --arg name "api_key" '.components.securitySchemes[$name]'` | `{"type":"apiKey","name":"api_key","in":"header"}` |
| `examples/stripe/stripe-subset.json` | `jaq '[.components.securitySchemes \| keys[]]'` | `["basicAuth","bearerAuth"]` |
| `examples/stripe/stripe-subset.json` | `jaq --arg name "bearerAuth" '.components.securitySchemes[$name].scheme'` | `"bearer"` |
| `examples/github/github-subset.json` | `jaq '[.components.securitySchemes // {} \| keys[]]'` | `[]` |
