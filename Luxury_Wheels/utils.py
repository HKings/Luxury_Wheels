

# Está função verifica se o nome do arquivo contém um ponto (.), o que indica a presença de uma extensão como PNG,
# JPNG por exemplo. Ela também divide o nome do arquivo a partir do último ponto, pegando a última parte (a extensão)
# filename.rsplit('.', 1)[1], converte a extensão para minúsculas para fazer uma comparação case-insensitive .lower()
# e verifica se a extensão está na lista de extensões permitidas.
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS