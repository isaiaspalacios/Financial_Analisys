# ===========================================================================
#   ENTREGA UNA TABLA CON UN SEMAFORO 
#  │ Criptomoneda   │ Precio USD   │ RSI                   │ MACD        
#   Version: 3
#   Fecha 12/07/25
#   Cluade
# ===========================================================================

import requests
import pandas as pd
import ta
from tabulate import tabulate
from colorama import Fore, Style, init
import time
import numpy as np

init(autoreset=True)

criptos = {
    "Bitcoin": "bitcoin",
    "Ethereum": "ethereum",
    "Solana": "solana",
    "Cardano": "cardano",
    "XRP": "ripple",
    "Immutable X": "immutable-x"  # Agregado IMX
}

def obtener_datos(coin_id, dias=30, reintentos=3):
    """
    Obtiene datos de precios con manejo de errores y reintentos
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart"
    params = {"vs_currency": "usd", "days": dias, "interval": "daily"}
    
    for intento in range(reintentos):
        try:
            print(f"Obteniendo datos para {coin_id}... (intento {intento + 1})")
            r = requests.get(url, params=params, timeout=10)
            r.raise_for_status()  # Lanza excepción si hay error HTTP
            
            data = r.json()
            if "prices" not in data:
                print(f"Error: No se encontraron datos de precios para {coin_id}")
                return None
                
            precios = data["prices"]
            if len(precios) < 20:  # Necesitamos suficientes datos para MACD
                print(f"Error: Datos insuficientes para {coin_id}")
                return None
                
            df = pd.DataFrame(precios, columns=["timestamp", "price"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)
            df = df.sort_index()  # Asegurar orden cronológico
            
            return df
            
        except requests.exceptions.RequestException as e:
            print(f"Error de conexión para {coin_id} (intento {intento + 1}): {e}")
            if intento < reintentos - 1:
                time.sleep(2)  # Esperar antes del siguiente intento
            continue
        except Exception as e:
            print(f"Error inesperado para {coin_id}: {e}")
            return None
    
    return None

def analizar(df):
    """
    Calcula RSI y MACD con validación de datos
    """
    if df is None or len(df) < 20:
        return None
    
    try:
        # Calcular RSI
        df['rsi'] = ta.momentum.RSIIndicator(df['price'], window=14).rsi()
        
        # Calcular MACD con parámetros estándar
        macd_indicator = ta.trend.MACD(df['price'], window_fast=12, window_slow=26, window_sign=9)
        df['macd'] = macd_indicator.macd()
        df['macd_signal'] = macd_indicator.macd_signal()
        df['macd_histogram'] = macd_indicator.macd_diff()
        
        # Verificar que tenemos datos válidos
        if df['macd_signal'].isna().all():
            print("Advertencia: No se pudo calcular MACD signal")
            return None
            
        return df
        
    except Exception as e:
        print(f"Error al calcular indicadores: {e}")
        return None

def interpretar_señales(df):
    """
    Interpreta las señales de RSI y MACD
    """
    if df is None:
        return "Error", "Error", "Error"
    
    try:
        # Obtener últimos valores válidos
        ult = df.dropna().iloc[-1]
        
        rsi = ult['rsi']
        macd = ult['macd']
        macd_sig = ult['macd_signal']
        precio = ult['price']
        
        def semaforo(valor):
            if "Compra" in valor:
                return Fore.GREEN + "🟢 " + valor + Style.RESET_ALL
            elif "Venta" in valor:
                return Fore.RED + "🔴 " + valor + Style.RESET_ALL
            else:
                return Fore.YELLOW + "🟡 " + valor + Style.RESET_ALL

        # Interpretación RSI
        if pd.isna(rsi):
            rsi_msg = "Sin datos"
        elif rsi < 30:
            rsi_msg = "Compra (Sobreventa)"
        elif rsi > 70:
            rsi_msg = "Venta (Sobrecompra)"
        else:
            rsi_msg = "Neutro"

        # Interpretación MACD
        if pd.isna(macd) or pd.isna(macd_sig):
            macd_msg = "Sin datos"
        elif macd > macd_sig:
            macd_msg = "Compra (Alcista)"
        elif macd < macd_sig:
            macd_msg = "Venta (Bajista)"
        else:
            macd_msg = "Neutro"

        return semaforo(rsi_msg), semaforo(macd_msg), round(precio, 2)
        
    except Exception as e:
        print(f"Error al interpretar señales: {e}")
        return "Error", "Error", "Error"

def obtener_precio_actual(coin_id):
    """
    Obtiene el precio actual como respaldo
    """
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price"
        params = {"ids": coin_id, "vs_currencies": "usd"}
        r = requests.get(url, params=params, timeout=5)
        r.raise_for_status()
        data = r.json()
        return data[coin_id]["usd"]
    except:
        return None

def main():
    print(f"{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}🚀 ANALIZADOR DE CRIPTOMONEDAS - RSI & MACD")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    
    tabla = []
    
    for nombre, cid in criptos.items():
        print(f"\n{Fore.BLUE}Procesando {nombre}...{Style.RESET_ALL}")
        
        try:
            # Obtener y analizar datos
            df = obtener_datos(cid, dias=50)  # Más días para mejor cálculo de MACD
            
            if df is not None:
                df = analizar(df)
                
                if df is not None:
                    rsi, macd, precio = interpretar_señales(df)
                    tabla.append([nombre, f"${precio:,.2f}", rsi, macd])
                else:
                    # Intentar obtener solo el precio actual
                    precio_actual = obtener_precio_actual(cid)
                    if precio_actual:
                        tabla.append([nombre, f"${precio_actual:,.2f}", 
                                    Fore.YELLOW + "🟡 Sin datos RSI", 
                                    Fore.YELLOW + "🟡 Sin datos MACD"])
                    else:
                        tabla.append([nombre, "❌ Sin datos", "❌ Error", "❌ Error"])
            else:
                tabla.append([nombre, "❌ Sin datos", "❌ Error", "❌ Error"])
                
        except Exception as e:
            print(f"Error procesando {nombre}: {e}")
            tabla.append([nombre, "❌ Error", "❌ Error", "❌ Error"])
        
        # Pausa entre requests para evitar rate limiting
        time.sleep(1)
    
    print(f"\n{Fore.CYAN}{'='*70}")
    print(f"{Fore.CYAN}📊 RESULTADOS DEL ANÁLISIS TÉCNICO")
    print(f"{Fore.CYAN}{'='*70}{Style.RESET_ALL}")
    
    print(tabulate(tabla, headers=["Criptomoneda", "Precio USD", "RSI", "MACD"], 
                   tablefmt="fancy_grid"))
    
    print(f"\n{Fore.CYAN}📋 LEYENDA:")
    print(f"{Fore.GREEN}🟢 Compra: Señal alcista")
    print(f"{Fore.RED}🔴 Venta: Señal bajista") 
    print(f"{Fore.YELLOW}🟡 Neutro: Sin señal clara")
    print(f"{Style.RESET_ALL}")
    
    print(f"{Fore.MAGENTA}💡 RSI: <30 Sobreventa (Compra), >70 Sobrecompra (Venta)")
    print(f"{Fore.MAGENTA}💡 MACD: Línea > Señal (Compra), Línea < Señal (Venta){Style.RESET_ALL}")

if __name__ == "__main__":
    main()