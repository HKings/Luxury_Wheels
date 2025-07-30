# **Luxury Wheels - Sistema de Aluguer de Veículos**

Olá! O **Luxury Wheels** é um **sistema completo de gestão de aluguer de veículos** desenvolvido em Python com Flask que permite gerir eficientemente o aluguer de carros e motas. O sistema oferece funcionalidades completas tanto para clientes como para administradores, proporcionando uma experiência de utilizador intuitiva e robusta para a empresa fictícia "Luxury Wheels".

## **Funcionalidades**

### **Para Clientes**
* **Registo e Autenticação**: Sistema seguro de registo e login com encriptação de passwords
* **Pesquisa Avançada**: Encontrar veículos por tipo, marca, modelo, categoria, assentos e transmissão
* **Catálogo de Veículos**: Visualização em cards com paginação (10 veículos por página)
* **Galeria de Imagens**: Sistema completo de upload e visualização de múltiplas imagens por veículo
* **Sistema de Reservas**: Reservar veículos com cálculo automático de preços e duração
* **Carrinho de Compras**: Gestão de reservas antes da confirmação final
* **Perfil Pessoal**: Atualizar dados pessoais e consultar histórico de reservas
* **Estados em Tempo Real**: Verificação automática de disponibilidade dos veículos

### **Para Administradores**
* **Dashboard Analítico**: Estatísticas detalhadas de veículos por categoria (carros/motas disponíveis, reservados, em manutenção)
* **Gestão Completa de Veículos**: Adicionar, editar, remover e controlar estado dos veículos
* **Sistema de Estados Avançado**: Ativo, Em Manutenção, Reservado com agendamento de datas
* **Gestão de Imagens**: Upload, substituição e remoção de múltiplas imagens por veículo
* **Gestão de Clientes**: Pesquisar, visualizar, editar e remover dados dos clientes
* **Controlo de Manutenção**: Agendar períodos de manutenção com datas de início e fim
* **Categorização**: Sistema de categorias por tipo de veículo (Mini, Económico, Luxo, SUV, etc.)
* **Validação Robusta**: Validação de dados de veículos, preços e datas
* **Atualização Automática**: Sistema que atualiza estados automaticamente baseado no tempo

## **Porquê Este Projeto?**

Este projeto foi criado para demonstrar:
* **Arquitetura MVC**: Estrutura bem organizada seguindo padrões de desenvolvimento
* **Segurança**: Autenticação robusta com hash de passwords e controlo de acesso
* **Base de Dados**: Gestão eficiente com SQLAlchemy e relacionamentos complexos
* **Interface Moderna**: Templates responsivos com Bootstrap e JavaScript
* **Gestão de Estados**: Sistema inteligente de atualização automática de disponibilidade
* **Upload de Ficheiros**: Gestão segura de imagens com validação
* **Automação**: Agendamento automático de tarefas com APScheduler

## **Requisitos Técnicos**

* **Python 3.8+**
* **Flask 2.0+** - Framework web principal
* **SQLAlchemy** - ORM para gestão da base de dados  
* **Flask-Login** - Sistema de autenticação
* **Flask-Migrate** - Migrações da base de dados
* **APScheduler** - Agendamento automático de tarefas
* **Werkzeug** - Utilitários web e segurança
* **SQLite** - Base de dados (pode ser alterada para PostgreSQL/MySQL)

## **Como Executar**

1. **Clone o repositório**:
```bash
git clone https://github.com/HKings/luxury-wheels.git
cd luxury-wheels
```

2. **Crie um ambiente virtual (recomendado)**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

3. **Instale as dependências**:
```bash
pip install flask flask-sqlalchemy flask-login flask-migrate apscheduler werkzeug
```

4. **Configure as pastas necessárias**:
```bash
mkdir -p database static/uploads
```

5. **Execute a aplicação**:
```bash
python app.py
```

6. **Acesse a aplicação**:
- **Interface Principal**: http://localhost:5000
- **Área Administrativa**: http://localhost:5000/login_admin
  - **Utilizador**: admin1
  - **Password**: admin

## **Demonstração de Funcionalidades**

### **Registo de Novo Cliente**
```
1. Aceder a http://localhost:5000/registro
2. Preencher o formulário:
   - Nome: João
   - Apelido: Silva  
   - Email: joao.silva@email.com
   - Telefone: 912345678
   - Data de Nascimento: 1990-01-01
   - Morada: Rua das Flores, 123, Porto
   - NIF: 123456789
   - Password: ********

✅ Cliente registado com sucesso!
```

### **Pesquisa e Filtragem de Veículos**
```
1. Aceder a http://localhost:5000/list_vehicle
2. Utilizar os filtros disponíveis:
   - Tipo: Carro/Mota
   - Marca: BMW, Mercedes, Toyota, Honda...
   - Categoria: Mini, Económico, Luxo, SUV, Scooters...
   - Assentos: 2, 4, 5, 7+
   - Transmissão: Manual/Automática
   - Preço por dia

📋 Resultados apresentados em cards com paginação (10 por página)
```

### **Gestão Administrativa**
```
1. Login como admin: http://localhost:5000/login_admin
2. Dashboard mostra estatísticas em tempo real:
   - Carros disponíveis: X
   - Carros reservados: Y  
   - Carros em manutenção: Z
   - Total de clientes: W

3. Adicionar novo veículo com validação completa
4. Agendar manutenção com datas específicas
5. Upload de múltiplas imagens por veículo
```

## **Estrutura do Projeto**

```
luxury-wheels/
│
├── app.py                     # Aplicação principal Flask com configurações
├── models.py                  # Modelos da base de dados (Clientes, Admin, Veiculos, Reservation, Categoria)
├── admin.py                   # Blueprint de administração (CRUD veículos, clientes, dashboard)
├── auth.py                    # Sistema de autenticação (login, registo, logout)
├── user.py                    # Funcionalidades do cliente (perfil, carrinho, reservas)
├── views.py                   # Vistas e redirects auxiliares
├── urls.py                    # Rotas auxiliares
├── utils.py                   # Funções utilitárias (validação de ficheiros)
├── requirements.txt           # Dependências do projeto
├── database/
│   └── database.db           # Base de dados SQLite
├── static/
│   ├── css/                  # Folhas de estilo
│   │   ├── base.css          # Estilos base
│   │   ├── admin.css         # Estilos da área administrativa
│   │   ├── home.css          # Estilos da página inicial
│   │   └── client.css        # Estilos da área do cliente
│   ├── js/                   # Scripts JavaScript
│   ├── img/                  # Imagens estáticas (logos, favicons)
│   │   └── favicon/          # Ícones da aplicação
│   └── uploads/              # Imagens dos veículos carregadas pelos utilizadores
├── templates/
│   ├── base.html             # Template base principal
│   ├── base_admin.html       # Template base para administração
│   ├── home.html             # Página inicial
│   ├── login.html            # Página de login de clientes
│   ├── login_admin.html      # Página de login de administradores
│   ├── registro.html         # Página de registo
│   ├── list_vehicle.html     # Listagem de veículos para aluguer
│   ├── admin/                # Templates de administração
│   │   ├── admin_home.html   # Dashboard administrativo
│   │   ├── clients.html      # Gestão de clientes
│   │   ├── edit_clients.html # Edição de clientes
│   │   ├── search_vehicles.html # Pesquisa de veículos
│   │   ├── add_vehicles.html # Adicionar veículos
│   │   ├── edit_vehicle.html # Edição de veículos
│   │   ├── edit_type.html    # Edição de tipo de veículo
│   │   ├── toggle_status.html # Alteração de estado
│   │   └── replace_img.html  # Gestão de imagens
│   └── user/                 # Templates do utilizador
│       ├── client_perfil.html # Perfil do cliente
│       └── view_cart.html    # Carrinho de compras
└── README.md                 # Documentação do projeto
```

## **Principais Funcionalidades Técnicas**

### **Arquitetura e Base de Dados**
* **Modelo MVC**: Separação clara entre Models (models.py), Views (templates/) e Controllers (blueprints)
* **Relacionamentos Complexos**: Foreign keys entre Clientes, Veículos, Reservas e Categorias
* **Enumerações**: VehicleType (CARRO/MOTA) para controlo rigoroso de tipos
* **Indexação**: Campos críticos indexados para pesquisas eficientes (marca, modelo, email, NIF)

### **Sistema de Autenticação e Segurança**
* **Hash de Passwords**: Werkzeug PBKDF2 com salt para encriptação segura
* **Sessões Temporizada**: Timeout automático de 30 minutos
* **Controlo de Acesso**: Decorators personalizados (@admin_required)
* **Tipos de Utilizador**: Sistema dual com prefixos ('client_', 'admin_')
* **Validação de Uploads**: Extensões permitidas (PNG, JPG, JPEG, GIF) com secure_filename()

### **Gestão de Estados Dinâmica**
* **Estados de Veículo**: Disponível, Reservado, Em Manutenção, Indisponível
* **Atualização Automática**: APScheduler verifica estados a cada minuto
* **Lógica Temporal**: Veículos tornam-se disponíveis automaticamente após manutenção/reserva
* **Transições Inteligentes**: Sistema previne conflitos de estado

## **Funcionalidades Técnicas Avançadas**

### **Validação Robusta**
```python
def validate_vehicle_data(form_data):
    errors = []
    
    # Validação de ano (1900 - ano atual)
    year = int(form_data['year'])
    if year < 1900 or year > datetime.now().year:
        errors.append('Ano inválido!')
    
    # Validação de preço positivo
    price = float(form_data['price_per_day'])
    if price <= 0:
        errors.append('Preço deve ser maior que zero!')
        
    return errors
```

### **Atualização Automática de Estados**
```python
@classmethod
def update_all_vehicles_availability(cls):
    """APScheduler executa esta função a cada minuto"""
    vehicles = cls.query.filter(
        or_(cls.maintenance_end.isnot(None),
            cls.available_from.isnot(None))
    ).all()
    
    for vehicle in vehicles:
        if vehicle.maintenance_end and datetime.now() > vehicle.maintenance_end:
            vehicle.status = True
            vehicle.in_maintenance = False
```

### **Sistema de Upload Seguro**
```python
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
```

## **Melhorias Futuras Planeadas**

* **Sistema de Pagamentos**: Integração com Stripe/PayPal
* **Notificações Push**: Emails automáticos para confirmações e lembretes
* **Analytics Avançadas**: Dashboards com gráficos de utilização e receitas
* **API REST**: Endpoints para integração com apps móveis
* **Sistema de Avaliações**: Reviews e ratings dos veículos
* **Geolocalização**: Mapa interativo com localização dos veículos
* **App Móvel**: Aplicação nativa iOS/Android
* **Inteligência Artificial**: Recomendações personalizadas de veículos

## **Categorias de Veículos Disponíveis**

### **Carros**
* **Mini** - Veículos compactos para cidade
* **Económico** - Opção económica com baixo consumo
* **Compacto** - Equilíbrio entre espaço e eficiência
* **Intermédio** - Conforto para viagens médias
* **Familiar** - Espaço amplo para famílias
* **Luxo** - Veículos premium com todas as comodidades
* **Descapotável** - Para experiências únicas
* **SUV** - Versatilidade todo-o-terreno
* **Comercial** - Para necessidades profissionais

### **Motas**
* **Scooters** - Mobilidade urbana eficiente
* **Turismo** - Conforto para viagens longas
* **Desportivas** - Performance e adrenalina
* **Aventura** - Versatilidade on/off-road
* **Off-Road** - Especialização todo-o-terreno

## **Licença**

Este projeto está licenciado sob a Licença MIT - consulte o arquivo LICENSE para mais detalhes.

## **Autor**

**Hamilton P C Reis**
* GitHub: [@HKings](https://github.com/HKings)
* Email: hamiltonpcreis.eng@gmail.com
* Repositório Contact Agenda: [HKings](https://github.com/HKings)

## **Agradecimentos**

* Aos orientadores da escola Tokio School 
* Desenvolvido com Flask e SQLAlchemy
* Interface criada com Bootstrap
* Inspirado na necessidade de um sistema moderno de aluguer de veículos
* Agradecimentos especiais à comunidade Python pelo excelente suporte

**Se este projeto foi útil, considere dar uma estrela!** ⭐

---

*Sistema desenvolvido como projeto de final de curso em 2025 por Hamilton P C Reis - Demonstração prática de desenvolvimento web com Python/Flask seguindo as melhores práticas da indústria*