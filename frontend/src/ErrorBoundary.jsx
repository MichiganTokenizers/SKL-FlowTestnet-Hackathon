import React from 'react';

class ErrorBoundary extends React.Component {
    state = { hasError: false, error: null };

    static getDerivedStateFromError(error) {
        // Update state so the next render shows the fallback UI
        return { hasError: true, error };
    }

    componentDidCatch(error, errorInfo) {
        // Log the error to the console for debugging
        console.error('Error caught by ErrorBoundary:', error, errorInfo);
    }

    render() {
        if (this.state.hasError) {
            // Fallback UI when an error occurs
            return (
                <div className="container p-4">
                    <h1 className="display-4 fw-bold mb-4">Something Went Wrong</h1>
                    <p className="text-danger">{this.state.error?.message || 'An unexpected error occurred.'}</p>
                    <button
                        className="btn btn-primary"
                        onClick={() => window.location.reload()}
                    >
                        Reload Page
                    </button>
                </div>
            );
        }
        // Render children if no error
        return this.props.children;
    }
}

export default ErrorBoundary;