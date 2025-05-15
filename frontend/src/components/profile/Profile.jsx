import { useState, useEffect } from 'react';

const API_BASE_URL = "http://localhost:5000";

function Profile() {
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const sessionToken = localStorage.getItem('sessionToken');
        if (!sessionToken) {
            setError('Please log in to view your profile.');
            setLoading(false);
            return;
        }

        fetch(`${API_BASE_URL}/auth/verify`, {
            headers: { 'Authorization': sessionToken }
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    setProfile({ wallet_address: data.walletAddress });
                    setLoading(false);
                } else {
                    setError(data.error || 'Failed to fetch profile');
                    setLoading(false);
                }
            })
            .catch(err => {
                setError('Error fetching profile: ' + err.message);
                setLoading(false);
            });
    }, []);

    if (loading) return <p className="text-center text-muted">Loading profile...</p>;
    if (error) return <p className="text-center text-danger">{error}</p>;

    return (
        <div className="container p-4">
            <h1 className="display-4 fw-bold mb-4">Profile</h1>
            <p><strong>Wallet Address:</strong> {profile.wallet_address}</p>
            <p><strong>Username:</strong> {profile.username || 'Not set'}</p>
        </div>
    );
}

export default Profile; 