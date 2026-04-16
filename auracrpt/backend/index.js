const express = require('express');
const cors = require('cors');
const multer = require('multer');
const crypto = require('crypto');
require('dotenv').config();

const supabase = require('./database');
const { generateKeyPair, encryptMessage, decryptMessage } = require('./cryptoService');
const { embedMessage, extractMessage, generateNoiseWav } = require('./stegoService');
const { idsMiddleware, verifyToken, requireRole } = require('./middleware');

const app = express();
app.use(express.json());
app.use(cors());
app.use(idsMiddleware); // Apply IDS globally

const upload = multer({ storage: multer.memoryStorage() });

// --- AUTH SETUP (Runs after frontend Supabase Auth) ---
app.post('/api/auth/setup', verifyToken, async (req, res) => {
    const { username, role } = req.body;
    if (!username || !role) return res.status(400).json({ error: 'Missing fields' });
    
    try {
        // 1. Create Profile
        const { error: profileError } = await supabase
            .from('profiles')
            .upsert({ id: req.userId, username, role });
        
        if (profileError) throw profileError;

        // 2. Generate and Store RSA Keys
        const { publicKey, privateKey } = generateKeyPair();
        const { error: keyError } = await supabase
            .from('keys')
            .upsert({ user_id: req.userId, public_key: publicKey, private_key: privateKey });
        
        if (keyError) throw keyError;

        res.json({ message: 'Identity Vault initialized successfully!' });
    } catch (err) {
        res.status(500).json({ error: err.message });
    }
});

app.get('/api/users/receivers', verifyToken, async (req, res) => {
    const { data, error } = await supabase
        .from('profiles')
        .select('id, username')
        .eq('role', 'Receiver');
    
    if (error) return res.status(500).json({ error: error.message });
    res.json(data);
});

// --- CORE VAULT ---
app.post('/api/vault/embed', verifyToken, requireRole('Sender'), upload.single('audio'), async (req, res) => {
    const { message, recipientId, autoGenerate } = req.body;
    if (!message || !recipientId) return res.status(400).json({ error: 'Missing message or recipientId' });
    if (!req.file && String(autoGenerate) !== 'true') return res.status(400).json({ error: 'Missing audio file or autoGenerate flag' });

    try {
        // 1. Get recipient public key
        const { data: keyRow, error: keyError } = await supabase
            .from('keys')
            .select('public_key')
            .eq('user_id', recipientId)
            .single();
        
        if (keyError || !keyRow) return res.status(400).json({ error: 'Recipient key not found' });
        
        // 2. Encrypt
        const encryptedStr = encryptMessage(keyRow.public_key, message);
        
        // 3. Embed (Steganography)
        let audioBuffer = req.file ? req.file.buffer : generateNoiseWav(3);
        const stegoBuffer = embedMessage(audioBuffer, encryptedStr);
        
        // 4. Save to Supabase Storage
        const fileId = crypto.randomBytes(16).toString('hex');
        const filename = `${fileId}.wav`;
        
        const { error: uploadError } = await supabase.storage
            .from('vault')
            .upload(filename, stegoBuffer, { contentType: 'audio/wav' });

        if (uploadError) throw uploadError;
        
        // 5. Insert Message Record
        const { error: dbError } = await supabase
            .from('messages')
            .insert({ 
                filename, 
                file_hash: fileId, 
                sender_id: req.userId, 
                recipient_id: recipientId 
            });

        if (dbError) {
            // Rollback Storage
            await supabase.storage.from('vault').remove([filename]);
            throw dbError;
        }

        res.json({ message: 'Secure payload generated and dispatched to Cloud Vault.' });
    } catch(e) {
        res.status(400).json({ error: e.message });
    }
});

app.get('/api/vault/inbox', verifyToken, requireRole('Receiver'), async (req, res) => {
    const { data, error } = await supabase
        .from('messages')
        .select(`
            id, 
            uploaded_at, 
            profiles:sender_id ( username )
        `)
        .eq('recipient_id', req.userId)
        .order('uploaded_at', { ascending: false });

    if (error) return res.status(500).json({ error: error.message });

    // Flatten for frontend
    const inbox = data.map(m => ({
        id: m.id,
        uploaded_at: m.uploaded_at,
        senderName: m.profiles.username
    }));

    res.json(inbox);
});

app.post('/api/vault/extract', verifyToken, requireRole('Receiver'), async (req, res) => {
    const { messageId } = req.body;
    if (!messageId) return res.status(400).json({ error: 'Missing messageId' });

    try {
        // 1. Get message metadata
        const { data: msgRow, error: msgError } = await supabase
            .from('messages')
            .select('filename')
            .eq('id', messageId)
            .eq('recipient_id', req.userId)
            .single();

        if (msgError || !msgRow) return res.status(404).json({ error: 'Message not found in inbox' });
        
        // 2. Get private key
        const { data: keyRow, error: keyError } = await supabase
            .from('keys')
            .select('private_key')
            .eq('user_id', req.userId)
            .single();

        if (keyError || !keyRow) return res.status(400).json({ error: 'Private key not found' });
        
        // 3. Download from Storage
        const { data: fileData, error: downloadError } = await supabase.storage
            .from('vault')
            .download(msgRow.filename);

        if (downloadError) throw downloadError;
        
        const fileBuffer = Buffer.from(await fileData.arrayBuffer());

        // 4. Extract and Decrypt
        const extractedEncrypted = extractMessage(fileBuffer);
        const decryptedMessage = decryptMessage(keyRow.private_key, extractedEncrypted);
        
        // 5. BURN AFTER READING
        await supabase.storage.from('vault').remove([msgRow.filename]);
        await supabase.from('messages').delete().eq('id', messageId);

        res.json({ secret: decryptedMessage });
    } catch(e) {
        res.status(400).json({ error: 'Extraction failed: ' + e.message });
    }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`AuraCrypt backend running on port ${PORT}`);
});
