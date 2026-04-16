# AuraCrypt: Full-Stack Secure Audio Steganography Vault

**AuraCrypt** is an end-to-end secure, full-stack web application designed for stealth communication. It merges the disciplines of **Cryptography** (RSA-2048 Asymmetric Encryption) and **Steganography** (Least Significant Bit injection) to transmit highly confidential data hidden entirely within uncompressed audio `.wav` files. The platform is architected around absolute zero-trace principles, featuring a robust **"Burn-After-Reading"** execution flow that cryptographically destroys the data carrier upon a single successful read.

---

## 1. Core Mechanisms & Technologies Used

### A. The Cryptography Engine (`backend/cryptoService.js`)
To ensure total confidentiality *before* steganography is even applied, all plaintext is run through advanced asymmetric encryption.
* **Algorithm**: RSA (Rivest–Shamir–Adleman) with a strong `2048-bit` Modulus Length.
* **Format**: PEM encoded keys. SPKI format for Public Keys and PKCS8 for Private Keys.
* **Mechanism**: 
  1. When a user registers, Node.js native `crypto.generateKeyPairSync()` provisions a unique public/private key pair.
  2. The Sender selects a target Receiver. The backend fetches the target Receiver's **Public Key**.
  3. The Plaintext message is converted to an `utf8` Buffer and encrypted via `crypto.publicEncrypt()` using `RSA_PKCS1_OAEP_PADDING` with a `sha256` hashing function.
  4. Only the target Receiver holds the relative **Private Key** (locked in SQLite) necessary to reverse this cipher using `crypto.privateDecrypt()`.

### B. The Steganography Engine (`backend/stegoService.js`)
Hide-in-plain-sight data embedding utilizing the **wavefile** manipulation library.
* **Mechanism**: **Least Significant Bit (LSB) Modification**.
* **Flow**:
  1. An uncompressed 16-bit PCM Audio WAV file is obtained.
  2. The 16-bit Int16Array audio stream samples are flattened (to account for multi-channel stereo complexities).
  3. The length of the upcoming encrypted payload is converted to a **32-bit signed integer**. The code forcibly rewrites the very last bit (the LSB via `(flatSamples[sampleIdx] & ~1) | bit`) of the first 32 audio samples to encode this length dynamically.
  4. The process iterates over the Base64-encrypted payload string, byte by byte. Every byte is broken down into 8 individual bits. Each bit overwrites the LSB of consecutive audio samples. This results in microscopic, inaudible static variations in the audio file containing a perfectly retrievable data structure.
  5. The altered samples are reconstructed (`fromScratch`) back into a valid WAV blob buffer. 

### C. Auto-Generated White Noise Carrier
To drastically simplify UX and obscure traffic footprints, Senders do not actually need to supply an audio file. If the `autoGenerate` flag is activated, the backend invokes `generateNoiseWav(seconds = 3)`.
* **Mechanism**: It loops through `44100 * 3` Int16 representations (a 3-second 44.1kHz buffer) invoking `Math.random() * 65535 - 32768`. It generates pure mathematical "white noise"—the *perfect* camouflage for LSB steganography because random noise distributions easily mask injected bit variations.

### D. Intrusion Detection System (IDS) & Auth (`backend/middleware.js`)
Security is managed across all HTTP requests using active tracking.
* **JWT Authentication**: Active JSON Web Tokens (2-hour expiration, hashed via a secure `JWT_SECRET`) lock all endpoints strictly to verified accounts.
* **Role-Based Access Control (RBAC)**: Enforced via `requireRole()`.
  * **Senders**: Can strictly query Receiver listings, upload files, and trigger the vault embed script. Senders cannot extract messages.
  * **Receivers**: Can strictly fetch their inbox list and trigger extraction sequences.
* **Active Intrusion Detection System (IDS)**: An in-memory Map structure watches the requesting IPs. It operates a rolling `60-second window`. If an IP issues more than `50 requests/minute`, the IDS interprets it as a DoS / brute-force trajectory and hard-blocks the IP by dumping `HTTP 429` errors with a tracked alert. 

### E. Burn-After-Reading Storage Vault
* **Mechanism**: When a payload successfully navigates the pipeline, the resulting WAV is stored inside a strict backend filesystem directory called `/vault_storage/` under an unguessable 16-byte hex serialized filename (via `crypto.randomBytes()`).
* **The "Burn"**: The instant a Receiver successfully posts `/api/vault/extract`, the application invokes `fs.readFileSync()`, reverse-engineers the LSB data array, decrypts the RSA block, and **immediately permanently deletes** the source WAV file (`fs.unlinkSync()`) alongside a hard SQL deletion row wipe. The transport medium mathematically ceases to exist.

---

## 2. Platform Architecture

### The Backend Application Flow
* **Language & Framework**: Node.js utilizing Express (`express@5`).
* **Database Protocol**: SQLite3 (`database.js`).
* **Schema**:
   * `users`: Stores `id`, `username`, `password_hash` (`bcryptjs` cost=10), and strict `role`.
   * `keys`: Relates user IDs to their massive stringified PEM public and private key chains.
   * `messages`: The registry connecting a filepath, a completely random identity hash, sender ID, recipient ID, and a local timestamp.
* **Filesystem Handling**: `multer` middleware evaluates multipart form data locally in RAM (`memoryStorage()`) buffering the standard blob before sending it into the Stego Engine.

### The Frontend Application Flow
* **Language & Framework**: React 19 bootstrapped on Vite. Routing managed by `react-router-dom`.
* **Visual Language**: Completely bespoke interface styled with custom CSS variables using premium Glassmorphism traits. 
   * Includes structural elements like `backdrop-filter: blur(12px)`.
   * Floating `.glass-card` elements with dynamic shadow transformations bounding state layouts.
   * Radial gradient backgrounds matching the brand palette.
   * Topography driven by `Outfit` (Headers) and `Inter` (Body). Iconography supplied by `Lucide-React`.
* **Client Layout (`App.jsx`)**:
   * **State Cache**: Keeps session alignment synchronized securely in `.localStorage`.
   * **Authentication Gateway**: Single dynamic conditional component rendering either Login or Register modes based on user intent.
   * **Sender Dashboard (`/dashboard`)**: Conditional UI layout for 'Senders'. Polls the `/users/receivers` block to fill select options. Handles file Drag-and-Drop parameters to conditionally mutate between generic File inputs and the "Auto-Generate White Noise" flag trigger.
   * **Receiver Dashboard (`/dashboard`)**: Conditional UI mapping user messages dynamically. Maps pending extractions. On "Extract & Burn" action completion, it parses the JSON promise and beautifully renders the secret contents directly into the browser DOM in a verified overlay wrapper, stripping the entry visually from the HTML listing simultaneously.

---

## 3. Directory Layout Blueprint

```text
CS_project/
├── auracrpt/
│   ├── backend/
│   │   ├── cryptoService.js      // Core logic for RSA-OAEP Keypairs & Encrypting
│   │   ├── stegoService.js       // Core logic for Int16 Array LSB mutations & Audio Masking
│   │   ├── database.js           // SQLite Schema scaffolding & Table Instantiation
│   │   ├── index.js              // Main Express Application & Endpoint Router
│   │   ├── middleware.js         // Express Pipeline (JWT Interceptors & IDS Blockers)
│   │   ├── package.json          // Backend Node dependencies
│   │   └── vault_storage/        // Directory: Physically restricted repository for live WAVs
│   │
│   └── frontend/
│       ├── src/
│       │   ├── App.jsx           // React Master Tree, Routing logic, Vault UI logic 
│       │   ├── index.css         // Master styling definitions and variables
│       │   └── main.jsx          // React DOM Binding
│       ├── index.html            // Core Vite DOM mapping
│       ├── vite.config.js        // Node build system orchestrator
│       └── package.json          // Frontend React/Vite dependencies
└── README.md
```

*(Note: Parent directory might carry scaffold `package.json` data for monolithic Next.js deployments, but AuraCrypt functions discretely inside `/auracrpt/`)*

---

## 4. Total Setup & Operational Walkthrough

**Global Prerequisites:** Node.js v18.x+, `npm`. 

### Initializing the Express Vault (Backend)
1. Open a terminal instance and resolve to the application root.
2. Enter the backend context: `cd auracrpt/backend`
3. Download framework modules: `npm install`
4. Spin up the pipeline: `node index.js` (Or `npm start`). 
   * *Status: The pipeline generates localized `auracrypt.db`, secures `vault_storage` folder, and binds to `http://localhost:3000` listening for CORS-verified requests.*

### Initializing the Client Console (Frontend)
1. Open a second detached terminal instance.
2. Enter the frontend workspace: `cd auracrpt/frontend`
3. Resolve UI Dependencies: `npm install`
4. Start the Hot-Module-Replacement UI Engine: `npm run dev`
   * *Status: Vite exposes a secure listener strictly mapped into `http://localhost:5173`. Open this URL inside any chromium or modern canvas browser.*

### Running an E2E Simulation
1. **Node A (Sender)**: Open localhost:5173. Select Register -> Sender -> Create Identity. Log in. Leave tab open.
2. **Node B (Receiver)**: Open an Incognito window to localhost:5173. Select Register -> Receiver -> Create Identity. Log in. Leave tab open.
3. Refresh Sender Tab. Ensure the target Receiver is active in the dropdown. 
4. Punch in a Secret payload. Choose to generate White noise. **Dispatch**. 
5. Switch to Receiver Window. See payload logged with timestamp. Click **Extract & Burn**. 
6. Watch UI seamlessly print the cryptographic success message. Under the hood, check `/vault_storage/` in your IDE context — you will see that the `.wav` file was completely exterminated.
