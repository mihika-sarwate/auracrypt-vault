const supabase = require('./database');

// Simple in-memory rate limiting / IDS
const rateLimits = new Map();

function idsMiddleware(req, res, next) {
    const ip = req.ip || req.connection.remoteAddress;
    const now = Date.now();
    
    if(!rateLimits.has(ip)) {
        rateLimits.set(ip, { count: 1, lastReq: now });
        return next();
    }
    
    let info = rateLimits.get(ip);
    
    // Time window: 1 minute
    if (now - info.lastReq > 60000) {
        info.count = 1;
        info.lastReq = now;
        return next();
    }
    
    info.count++;
    info.lastReq = now;
    
    // If more than 50 requests in a minute, Block.
    if (info.count > 50) {
        return res.status(429).json({ error: 'IDS Alert: IP Blocked due to suspected DoS attack or brute force.' });
    }
    
    next();
}

async function verifyToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    if (!authHeader) return res.status(403).json({ error: 'No token provided' });
    
    const token = authHeader.split(' ')[1] || authHeader;

    const { data: { user }, error } = await supabase.auth.getUser(token);

    if (error || !user) {
        return res.status(401).json({ error: 'Unauthorized: Invalid token' });
    }

    // Fetch role from profiles table
    const { data: profile, error: profileError } = await supabase
        .from('profiles')
        .select('role')
        .eq('id', user.id)
        .single();

    if (profileError || !profile) {
        return res.status(403).json({ error: 'User profile not found' });
    }

    req.userId = user.id;
    req.userRole = profile.role;
    next();
}

function requireRole(role) {
    return (req, res, next) => {
        if (req.userRole !== role && req.userRole !== 'Admin') {
            return res.status(403).json({ error: `Forbidden: Requires ${role} role` });
        }
        next();
    };
}

module.exports = { idsMiddleware, verifyToken, requireRole };
