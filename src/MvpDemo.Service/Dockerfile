# ============================================
# Stage 1: Build
# ============================================
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src

# Copy csproj files and restore
COPY MvpDemo.Service/MvpDemo.Service.csproj ./MvpDemo.Service/
COPY ISC.Observability/ISC.Observability.csproj ./ISC.Observability/
RUN dotnet restore ./MvpDemo.Service/MvpDemo.Service.csproj

# Copy everything else and build
COPY . .
RUN dotnet publish MvpDemo.Service/MvpDemo.Service.csproj -c Release -o /app/publish

# ============================================
# Stage 2: Runtime
# ============================================
FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser

COPY --from=build /app/publish .

# Switch to non-root user
USER appuser

EXPOSE 8080

HEALTHCHECK --interval=10s --timeout=3s --retries=5 --start-period=10s \
  CMD curl -sf http://localhost:8080/healthz || exit 1

ENTRYPOINT ["dotnet", "MvpDemo.Service.dll"]
