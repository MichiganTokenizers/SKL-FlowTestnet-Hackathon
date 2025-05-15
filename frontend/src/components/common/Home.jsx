import { Link } from 'react-router-dom';

function Home({ sessionToken, onLogout }) {
    return (
        <div className="container-fluid px-4 py-5">
            {sessionToken ? (
                <div className="row justify-content-center">
                    <div className="col-md-8">
                        <p className="lead">Welcome, {localStorage.getItem('walletAddress')}!</p>
                        <div className="mt-3">
                            <Link to="/sleeper-import" className="btn btn-primary">Import Sleeper League</Link>
                        </div>
                    </div>
                </div>
            ) : (
                <div className="row justify-content-center text-center">
                    <div className="col-md-8">
                        <h2 className="display-4 mb-4">Welcome to Supreme Keeper League</h2>
                        <p className="lead text-muted">Please connect your TON wallet to get started</p>
                    </div>
                </div>
            )}
            {sessionToken && (
                <div className="mt-3">
                    <button onClick={onLogout} className="btn btn-outline-danger">Logout</button>
                </div>
            )}
        </div>
    );
}

export default Home; 