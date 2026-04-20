# Init 脚本配方（Init Script Recipes）

生成 `init.sh` / `init.ps1` 环境引导脚本的模板与最佳实践。根据设计文档中的技术栈与环境管理器，选择匹配的配方。

## 通用规则

1. **幂等（Idempotent）** — 重复执行脚本绝不能破坏已有的可用环境
2. **跨平台（Cross-platform）** — 同时生成 `init.sh`（bash）与 `init.ps1`（PowerShell）
3. **快速失败（Fail-fast）** — 使用 `set -euo pipefail`（bash）/ `$ErrorActionPreference = "Stop"`（PowerShell）
4. **版本固定（Version-pinned）** — 按设计文档依赖表指定确切的运行时版本
5. **自诊断（Self-diagnosing）** — 末尾打印检测到的工具版本；任一失败退出码非零
6. **无交互提示（No interactive prompts）** — 所有回答必须自动接受（`-y` 标志、`--yes` 等）
7. **可移植路径（Portable paths）** — 使用 `"$(dirname "$0")"`（bash）/ `$PSScriptRoot`（PowerShell）定位项目根

## 脚本骨架

### init.sh (bash)

```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== [Project Name] Environment Bootstrap ==="

# --- Step 1: Runtime version ---
# [detect/install runtime]

# --- Step 2: Environment creation ---
# [create isolated environment]

# --- Step 3: Activate environment ---
# [activate for current shell]

# --- Step 4: Install dependencies ---
# [install packages]

# --- Step 5: Install dev tools ---
# [install test/coverage tools]

# --- Step 6: Verify ---
echo ""
echo "=== Environment Check ==="
# [print tool versions]
echo ""
echo "Environment ready."
```

### init.ps1 (PowerShell)

```powershell
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "=== [Project Name] Environment Bootstrap ==="

# --- Step 1: Runtime version ---
# [detect/install runtime]

# --- Step 2: Environment creation ---
# [create isolated environment]

# --- Step 3: Activate environment ---
# [activate for current shell]

# --- Step 4: Install dependencies ---
# [install packages]

# --- Step 5: Install dev tools ---
# [install test/coverage tools]

# --- Step 6: Verify ---
Write-Host ""
Write-Host "=== Environment Check ==="
# [print tool versions]
Write-Host ""
Write-Host "Environment ready."
```

---

## Python 配方

### Miniconda / Conda / Mamba

当设计文档指定 conda、miniconda 或 mamba 作为环境管理器时使用。常见于数据科学、机器学习及需要非 Python 系统依赖的项目。

**init.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

ENV_NAME="project-env"
PYTHON_VERSION="3.11"  # from design doc

echo "=== Environment Bootstrap (conda) ==="

# Detect conda/mamba
if command -v mamba &>/dev/null; then
    CONDA_CMD="mamba"
elif command -v conda &>/dev/null; then
    CONDA_CMD="conda"
else
    echo "ERROR: conda or mamba not found."
    echo "Install Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    echo "  curl -fsSL https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda.sh"
    echo "  bash miniconda.sh -b -p \$HOME/miniconda3"
    echo "  eval \"\$(\$HOME/miniconda3/bin/conda shell.bash hook)\""
    exit 1
fi

# Ensure conda is initialized for this shell
eval "$($CONDA_CMD shell.bash hook 2>/dev/null || true)"

# Create environment if not exists
if ! conda env list | grep -q "^${ENV_NAME} "; then
    echo "Creating conda environment '${ENV_NAME}' with Python ${PYTHON_VERSION}..."
    $CONDA_CMD create -n "$ENV_NAME" python="$PYTHON_VERSION" -y
else
    echo "Conda environment '${ENV_NAME}' already exists."
fi

# Activate
conda activate "$ENV_NAME"

# Install dependencies
if [ -f "environment.yml" ]; then
    echo "Installing from environment.yml..."
    $CONDA_CMD env update -n "$ENV_NAME" -f environment.yml --prune
elif [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt
fi

# Dev tools
pip install pytest pytest-cov mutmut

echo ""
echo "=== Environment Check ==="
echo "conda:   $($CONDA_CMD --version)"
echo "python:  $(python --version)"
echo "pytest:  $(pytest --version 2>&1 | head -1)"
echo ""
echo "Environment ready. Run: conda activate ${ENV_NAME}"
```

**init.ps1:**
```powershell
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$EnvName = "project-env"
$PythonVersion = "3.11"

Write-Host "=== Environment Bootstrap (conda) ==="

# Detect conda/mamba
$CondaCmd = $null
if (Get-Command mamba -ErrorAction SilentlyContinue) { $CondaCmd = "mamba" }
elseif (Get-Command conda -ErrorAction SilentlyContinue) { $CondaCmd = "conda" }
else {
    Write-Error "conda or mamba not found. Install Miniconda: https://docs.conda.io/en/latest/miniconda.html"
    exit 1
}

# Initialize conda for PowerShell
$condaHook = & conda shell.powershell hook 2>$null
if ($condaHook) { Invoke-Expression $condaHook }

# Create environment if not exists
$envExists = & conda env list | Select-String "^$EnvName\s"
if (-not $envExists) {
    Write-Host "Creating conda environment '$EnvName' with Python $PythonVersion..."
    & $CondaCmd create -n $EnvName python=$PythonVersion -y
} else {
    Write-Host "Conda environment '$EnvName' already exists."
}

# Activate
conda activate $EnvName

# Install dependencies
if (Test-Path "environment.yml") {
    Write-Host "Installing from environment.yml..."
    & $CondaCmd env update -n $EnvName -f environment.yml --prune
} elseif (Test-Path "requirements.txt") {
    Write-Host "Installing from requirements.txt..."
    pip install -r requirements.txt
}

# Dev tools
pip install pytest pytest-cov mutmut

Write-Host ""
Write-Host "=== Environment Check ==="
Write-Host "conda:   $(& $CondaCmd --version)"
Write-Host "python:  $(python --version)"
Write-Host "pytest:  $(pytest --version 2>&1 | Select-Object -First 1)"
Write-Host ""
Write-Host "Environment ready. Run: conda activate $EnvName"
```

### venv (stdlib)

当设计文档指定使用 Python venv 且无需 conda 时使用。

**init.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_VERSION="3.11"  # from design doc
VENV_DIR=".venv"

echo "=== Environment Bootstrap (venv) ==="

# Detect Python
PYTHON_BIN=""
for candidate in "python${PYTHON_VERSION}" "python3" "python"; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON_BIN="$candidate"
        break
    fi
done
if [ -z "$PYTHON_BIN" ]; then
    echo "ERROR: Python not found. Install Python >= ${PYTHON_VERSION}"
    exit 1
fi

# Version check
ACTUAL_VERSION=$($PYTHON_BIN -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Found Python ${ACTUAL_VERSION} at $(which $PYTHON_BIN)"

# Create venv if not exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_BIN -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists."
fi

# Activate
source "${VENV_DIR}/bin/activate"

# Upgrade pip
pip install --upgrade pip

# Install dependencies
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
fi
if [ -f "requirements-dev.txt" ]; then
    pip install -r requirements-dev.txt
fi

echo ""
echo "=== Environment Check ==="
echo "python:  $(python --version)"
echo "pip:     $(pip --version)"
echo "pytest:  $(pytest --version 2>&1 | head -1)"
echo ""
echo "Environment ready. Run: source ${VENV_DIR}/bin/activate"
```

**init.ps1:**
```powershell
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$VenvDir = ".venv"

Write-Host "=== Environment Bootstrap (venv) ==="

# Detect Python
$PythonBin = $null
foreach ($candidate in @("python3", "python")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $PythonBin = $candidate; break
    }
}
if (-not $PythonBin) { Write-Error "Python not found."; exit 1 }

# Create venv if not exists
if (-not (Test-Path $VenvDir)) {
    Write-Host "Creating virtual environment..."
    & $PythonBin -m venv $VenvDir
} else {
    Write-Host "Virtual environment already exists."
}

# Activate
& "$VenvDir\Scripts\Activate.ps1"

# Install
pip install --upgrade pip
if (Test-Path "requirements.txt") { pip install -r requirements.txt }
if (Test-Path "requirements-dev.txt") { pip install -r requirements-dev.txt }

Write-Host ""
Write-Host "=== Environment Check ==="
Write-Host "python:  $(python --version)"
Write-Host "pip:     $(pip --version)"
Write-Host ""
Write-Host "Environment ready. Run: & $VenvDir\Scripts\Activate.ps1"
```

### Poetry

**init.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Environment Bootstrap (poetry) ==="

if ! command -v poetry &>/dev/null; then
    echo "Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
fi

poetry config virtualenvs.in-project true
poetry install

echo ""
echo "=== Environment Check ==="
echo "poetry:  $(poetry --version)"
echo "python:  $(poetry run python --version)"
echo ""
echo "Environment ready. Run: poetry shell"
```

### uv

**init.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PYTHON_VERSION="3.11"  # from design doc

echo "=== Environment Bootstrap (uv) ==="

if ! command -v uv &>/dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

uv venv --python "$PYTHON_VERSION" .venv 2>/dev/null || true
source .venv/bin/activate
uv pip install -r requirements.txt

echo ""
echo "=== Environment Check ==="
echo "uv:      $(uv --version)"
echo "python:  $(python --version)"
echo ""
echo "Environment ready. Run: source .venv/bin/activate"
```

---

## Node.js 配方

### nvm

**init.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

NODE_VERSION="20"  # from design doc

echo "=== Environment Bootstrap (nvm) ==="

# Load nvm
export NVM_DIR="${NVM_DIR:-$HOME/.nvm}"
if [ -s "$NVM_DIR/nvm.sh" ]; then
    source "$NVM_DIR/nvm.sh"
elif [ -s "/usr/local/opt/nvm/nvm.sh" ]; then
    source "/usr/local/opt/nvm/nvm.sh"
else
    echo "ERROR: nvm not found."
    echo "Install: https://github.com/nvm-sh/nvm#installing-and-updating"
    exit 1
fi

# Install and use Node version
nvm install "$NODE_VERSION"
nvm use "$NODE_VERSION"

# Install dependencies
if [ -f "package-lock.json" ]; then
    npm ci
elif [ -f "yarn.lock" ]; then
    yarn install --frozen-lockfile
elif [ -f "pnpm-lock.yaml" ]; then
    pnpm install --frozen-lockfile
else
    npm install
fi

echo ""
echo "=== Environment Check ==="
echo "node:  $(node --version)"
echo "npm:   $(npm --version)"
echo ""
echo "Environment ready."
```

**init.ps1:**
```powershell
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$NodeVersion = "20"

Write-Host "=== Environment Bootstrap (nvm-windows) ==="

if (-not (Get-Command nvm -ErrorAction SilentlyContinue)) {
    Write-Error "nvm not found. Install nvm-windows: https://github.com/coreybutler/nvm-windows"
    exit 1
}

nvm install $NodeVersion
nvm use $NodeVersion

if (Test-Path "package-lock.json") { npm ci }
elseif (Test-Path "yarn.lock") { yarn install --frozen-lockfile }
elseif (Test-Path "pnpm-lock.yaml") { pnpm install --frozen-lockfile }
else { npm install }

Write-Host ""
Write-Host "=== Environment Check ==="
Write-Host "node:  $(node --version)"
Write-Host "npm:   $(npm --version)"
Write-Host ""
Write-Host "Environment ready."
```

### fnm

**init.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

NODE_VERSION="20"

echo "=== Environment Bootstrap (fnm) ==="

if ! command -v fnm &>/dev/null; then
    echo "Installing fnm..."
    curl -fsSL https://fnm.vercel.app/install | bash
    eval "$(fnm env)"
fi

fnm install "$NODE_VERSION"
fnm use "$NODE_VERSION"

npm ci

echo "node: $(node --version)"
echo "Environment ready."
```

---

## Java 配方

### SDKMAN!

**init.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

JAVA_VERSION="21.0.2-tem"  # from design doc (vendor-specific)

echo "=== Environment Bootstrap (sdkman) ==="

# Load SDKMAN
export SDKMAN_DIR="${SDKMAN_DIR:-$HOME/.sdkman}"
if [ -s "$SDKMAN_DIR/bin/sdkman-init.sh" ]; then
    source "$SDKMAN_DIR/bin/sdkman-init.sh"
else
    echo "ERROR: SDKMAN not found."
    echo "Install: curl -s https://get.sdkman.io | bash"
    exit 1
fi

sdk install java "$JAVA_VERSION" || true
sdk use java "$JAVA_VERSION"

# Build
if [ -f "mvnw" ]; then
    ./mvnw clean install -DskipTests
elif [ -f "gradlew" ]; then
    ./gradlew build -x test
fi

echo ""
echo "=== Environment Check ==="
echo "java:   $(java -version 2>&1 | head -1)"
echo "maven:  $(./mvnw --version 2>&1 | head -1)" 2>/dev/null || true
echo "gradle: $(./gradlew --version 2>&1 | grep Gradle)" 2>/dev/null || true
echo ""
echo "Environment ready."
```

---

## C/C++ 配方

### 系统包

**init.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Environment Bootstrap (C/C++) ==="

# Check compiler
if command -v gcc &>/dev/null; then
    echo "gcc: $(gcc --version | head -1)"
elif command -v clang &>/dev/null; then
    echo "clang: $(clang --version | head -1)"
else
    echo "ERROR: No C/C++ compiler found. Install gcc or clang."
    exit 1
fi

# Check cmake
if ! command -v cmake &>/dev/null; then
    echo "ERROR: cmake not found."
    exit 1
fi

# Build
mkdir -p build && cd build
cmake .. -DCMAKE_BUILD_TYPE=Debug
cmake --build .

echo ""
echo "=== Environment Check ==="
echo "cmake: $(cmake --version | head -1)"
echo ""
echo "Environment ready."
```

---

## Go 配方

### 系统 go / asdf

**init.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

GO_VERSION="1.22"  # from design doc
MODULE_PATH="example.com/project"  # from design doc

echo "=== Environment Bootstrap (Go) ==="

# Detect go
if ! command -v go &>/dev/null; then
    if command -v asdf &>/dev/null; then
        echo "go not found; installing via asdf..."
        asdf plugin-add golang || true
        asdf install golang "$GO_VERSION"
        asdf local golang "$GO_VERSION"
    else
        echo "ERROR: Go not found. Install from https://go.dev/dl/ or 'asdf plugin-add golang && asdf install golang $GO_VERSION'"
        exit 1
    fi
fi

# Module init (idempotent)
if [ ! -f "go.mod" ]; then
    go mod init "$MODULE_PATH"
fi

go mod tidy

# Dev tools
if ! command -v golangci-lint &>/dev/null; then
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
fi

echo ""
echo "=== Environment Check ==="
echo "go:             $(go version)"
echo "golangci-lint:  $(golangci-lint --version 2>&1 | head -1)"
echo ""
echo "Environment ready."
```

**init.ps1:**
```powershell
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

$GoVersion = "1.22"
$ModulePath = "example.com/project"

Write-Host "=== Environment Bootstrap (Go) ==="

if (-not (Get-Command go -ErrorAction SilentlyContinue)) {
    Write-Error "Go not found. Install from https://go.dev/dl/"
    exit 1
}

if (-not (Test-Path "go.mod")) {
    go mod init $ModulePath
}

go mod tidy

if (-not (Get-Command golangci-lint -ErrorAction SilentlyContinue)) {
    go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
}

Write-Host ""
Write-Host "=== Environment Check ==="
Write-Host "go:             $(go version)"
Write-Host ""
Write-Host "Environment ready."
```

---

## Docker / Devcontainer 配方

**init.sh:**
```bash
#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

echo "=== Environment Bootstrap (docker) ==="

if ! command -v docker &>/dev/null; then
    echo "ERROR: Docker not found. Install from https://docs.docker.com/get-docker/"
    exit 1
fi

if [ -f ".devcontainer/devcontainer.json" ]; then
    echo "Devcontainer config found. Use 'devcontainer up' or open in VS Code."
elif [ -f "docker-compose.yml" ] || [ -f "compose.yml" ]; then
    docker compose up -d --build
    echo "Services started."
elif [ -f "Dockerfile" ]; then
    docker build -t "$(basename "$PWD")" .
    echo "Image built."
fi

echo "Environment ready."
```

---

## 选型指引

根据设计文档的技术栈与约束选择对应配方：

| 设计文档中的信号 | 对应配方 |
|---|---|
| `environment.yml` 或列出 conda 包 | Miniconda / Conda / Mamba |
| Python + "虚拟环境" 或 venv | venv |
| `pyproject.toml` 含 `[tool.poetry]` | Poetry |
| `pyproject.toml` 提及 uv | uv |
| `.nvmrc` 或提及 nvm | nvm |
| `.node-version` 或提及 fnm | fnm |
| Java + 提及 SDKMAN | SDKMAN |
| `Dockerfile` 或 `docker-compose.yml` | Docker |
| 存在 `.devcontainer/` 目录 | Devcontainer |
| C/C++ 使用 CMake | 系统包 |
| Go + `go.mod` | 系统 go / asdf |
| 未指定环境管理器 | 使用语言默认（Python 用 venv，Node 用 nvm，Go 用系统 go） |

## 组合工具

项目可能需要多个工具，init 脚本应按顺序串起来：

```bash
# Example: Python (conda) + Node (nvm) + Docker (services)
# 1. Set up Python environment via conda
# 2. Set up Node environment via nvm
# 3. Start Docker services (databases, etc.)
# 4. Run database migrations
# 5. Verify all tools
```

每一步都必须幂等，并在末尾加上版本校验。
