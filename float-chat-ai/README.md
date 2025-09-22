# Float-Chat-AI 🌊

A conversational AI interface for exploring ARGO oceanographic data through natural language queries.

## Overview

Float-Chat-AI makes oceanographic data accessible to researchers, students, and analysts by providing a ChatGPT-like interface for querying ARGO float data. Ask questions in plain English and get intelligent responses with data visualizations.

### Key Features

- 💬 **Natural Language Queries**: Ask questions like "What's the average temperature at 1000m depth?"
- 📊 **Interactive Visualizations**: Automatic chart and table generation using Plotly
- 🌊 **ARGO Data Processing**: Built-in support for netCDF oceanographic datasets
- 🤖 **AI-Powered Responses**: Contextual explanations of oceanographic phenomena
- 🔄 **Session Management**: Persistent conversation history
- 🐳 **Docker Ready**: Complete containerized setup

## Architecture

### Backend (FastAPI)
- **Data Processing**: xarray/netCDF4 for oceanographic data
- **AI Integration**: OpenAI GPT or local LLM with fallback pattern matching
- **Database**: PostgreSQL for session management
- **Visualization**: Plotly for dynamic chart generation

### Frontend (React)
- **Chat Interface**: Modern conversational UI
- **Data Visualization**: React-Plotly integration
- **Responsive Design**: Mobile-friendly interface
- **Real-time Updates**: WebSocket-ready architecture

## Quick Start

### Prerequisites
- Docker and Docker Compose
- (Optional) OpenAI API key for enhanced AI features

### Installation

1. **Clone the repository**:
```bash
git clone <repository-url>
cd float-chat-ai
```

2. **Set up environment variables**:
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY (optional)
```

3. **Start with Docker Compose**:
```bash
docker-compose up --build
```

4. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Manual Setup (Development)

#### Backend Setup
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

#### Frontend Setup
```bash
cd frontend
npm install
npm start
```

#### Database Setup
```bash
# Start PostgreSQL locally or use Docker:
docker run -d --name postgres-float-chat \
  -e POSTGRES_DB=float_chat_ai \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 postgres:15-alpine
```

## Usage Examples

### Sample Queries
- "What's the average temperature at 500 meters depth?"
- "Show me a salinity profile"
- "Find the maximum temperature in the dataset"
- "What's the pressure at 2000m?"
- "Compare temperature and salinity at the surface"

### API Endpoints

- `POST /query` - Process natural language queries
- `GET /data/{id}` - Retrieve raw oceanographic data
- `GET /health` - Health check endpoint
- `GET /sessions/{id}/history` - Get conversation history

## Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/float_chat_ai

# AI Services (Optional)
OPENAI_API_KEY=your_openai_key_here

# Application
ENVIRONMENT=development
REACT_APP_API_URL=http://localhost:8000
```

### Data Sources

The prototype includes:
- **Mock ARGO data**: Realistic synthetic oceanographic profiles
- **Sample queries**: Pre-built SQL templates for common analyses
- **Extensible framework**: Easy integration with real ARGO data sources

## Development

### Project Structure
```
float-chat-ai/
├── backend/              # FastAPI backend
│   ├── main.py          # Application entry point
│   ├── services/        # Core services
│   │   ├── ai_service.py
│   │   ├── data_processor.py
│   │   └── database.py
│   └── requirements.txt
├── frontend/            # React frontend
│   ├── src/
│   │   ├── components/  # React components
│   │   ├── services/    # API services
│   │   └── App.js
│   └── package.json
├── data/               # Data files
│   ├── queries.sql     # Sample SQL queries
│   └── sample_argo.nc  # Mock netCDF data
└── docker-compose.yml  # Container orchestration
```

### Adding New Features

1. **New Query Types**: Extend pattern matching in `ai_service.py`
2. **Data Sources**: Add processors in `data_processor.py`
3. **Visualizations**: Enhance `DataVisualization.js` component
4. **UI Components**: Create new React components in `/components`

### Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
docker-compose -f docker-compose.test.yml up
```

## Deployment

### Production Setup
1. Set production environment variables
2. Configure SSL certificates
3. Set up monitoring and logging
4. Deploy with container orchestration (Kubernetes/Docker Swarm)

### Scaling Considerations
- Add Redis for session caching
- Implement rate limiting
- Use CDN for static assets
- Database read replicas for query performance

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## Roadmap

- [ ] Real ARGO data integration
- [ ] Advanced visualization types (3D plots, maps)
- [ ] Multi-language support
- [ ] Mobile app version
- [ ] Collaborative features
- [ ] Export to scientific formats (NetCDF, CSV)
- [ ] Integration with Jupyter notebooks

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **ARGO Program**: For providing global oceanographic data
- **FastAPI & React**: For excellent development frameworks
- **OpenAI**: For conversational AI capabilities
- **Plotly**: for interactive visualizations

## Support

For questions, issues, or contributions:
- 📧 Email: [your-email@domain.com]
- 🐛 Issues: [GitHub Issues]
- 📖 Documentation: [Project Wiki]

---

**Built for marine research accessibility** 🌊📊🤖