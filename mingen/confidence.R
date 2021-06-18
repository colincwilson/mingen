# A&H 2003, p.127
confidence = function(hits, scope, alpha=0.55) {
    p_star = (hits + 0.5) / (scope + 1.0)
    var_est = (p_star * (1 - p_star)) / scope
    var_est = var_est**0.5
    z = qt(alpha, scope - 1.0)
    c = p_star - z * var_est
    return (c)
}

