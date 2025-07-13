# ===========================================================================
#   ANALIZADOR CRYPTO - FASE 1 COMPLETA
#   Análisis Técnico Avanzado Multi-API
#         
#   Fecha 12/07/25
#   Claude
# ===========================================================================


import requests
import pandas as pd
import numpy as np
import ta
from tabulate import tabulate
from colorama import Fore, Style, init
import time
import warnings
from datetime import datetime, timedelta
import json
import os

warnings.filterwarnings('ignore')
init(autoreset=True)

# Configuración de APIs
API_CONFIG = {
    'coingecko': {
        'base_url': 'https://api.coingecko.com/api/v3',
        'rate_limit': 50,  # calls per minute
        'timeout': 10
    },
    'cryptocompare': {
        'base_url': 'https://min-api.cryptocompare.com/data/v2',
        'rate_limit': 100,
        'timeout': 10
    },
    'coincap': {
        'base_url': 'https://api.coincap.io/v2',
        'rate_limit': 200,
        'timeout': 10
    }
}

# Configuración de criptomonedas
CRYPTO_CONFIG = {
    "Bitcoin": {"coingecko": "bitcoin", "cryptocompare": "BTC", "coincap": "bitcoin"},
    "Ethereum": {"coingecko": "ethereum", "cryptocompare": "ETH", "coincap": "ethereum"},
    "Solana": {"coingecko": "solana", "cryptocompare": "SOL", "coincap": "solana"},
    "Cardano": {"coingecko": "cardano", "cryptocompare": "ADA", "coincap": "cardano"},
    "XRP": {"coingecko": "ripple", "cryptocompare": "XRP", "coincap": "ripple"},
    "Immutable X": {"coingecko": "immutable-x", "cryptocompare": "IMX", "coincap": "immutable-x"},
    "VET": {"coingecko": "vechain", "cryptocompare": "VET", "coincap": "vechain"},
    "UNI": {"coingecko": "uniswap", "cryptocompare": "UNI", "coincap": "uniswap"},
    "AAVE": {"coingecko": "aave", "cryptocompare": "AAVE", "coincap": "aave"},
    "AVAX": {"coingecko": "avalanche-2", "cryptocompare": "AVAX", "coincap": "avalanche"}
}

class CryptoAnalyzer:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 300  # 5 minutos
        self.api_status = self._test_apis()
        
    def _test_apis(self):
        """Prueba la disponibilidad de las APIs"""
        status = {}
        
        # Test CoinGecko
        try:
            response = requests.get(
                f"{API_CONFIG['coingecko']['base_url']}/ping",
                timeout=5
            )
            status['coingecko'] = response.status_code == 200
        except:
            status['coingecko'] = False
            
        # Test CryptoCompare
        try:
            response = requests.get(
                f"{API_CONFIG['cryptocompare']['base_url']}/price?fsym=BTC&tsym=USD",
                timeout=5
            )
            status['cryptocompare'] = response.status_code == 200
        except:
            status['cryptocompare'] = False
            
        # Test CoinCap
        try:
            response = requests.get(
                f"{API_CONFIG['coincap']['base_url']}/assets/bitcoin",
                timeout=5
            )
            status['coincap'] = response.status_code == 200
        except:
            status['coincap'] = False
            
        print(f"{Fore.CYAN}📡 Estado de APIs:")
        for api, working in status.items():
            color = Fore.GREEN if working else Fore.RED
            emoji = "✅" if working else "❌"
            print(f"{color}{emoji} {api.upper()}: {'Disponible' if working else 'No disponible'}")
        
        return status
    
    def _get_cache_key(self, crypto, timeframe, days):
        """Genera clave única para cache"""
        return f"{crypto}_{timeframe}_{days}"
    
    def _is_cache_valid(self, cache_key):
        """Verifica si el cache es válido"""
        if cache_key not in self.cache:
            return False
        
        timestamp = self.cache[cache_key]['timestamp']
        return (datetime.now() - timestamp).seconds < self.cache_duration
    
    def _get_from_coingecko(self, crypto_id, days=90):
        """Obtiene datos de CoinGecko - VERSIÓN MEJORADA"""
        try:
            # Solicitar más días para asegurar suficientes datos
            request_days = max(days, 200)  # Mínimo 200 días
            
            url = f"{API_CONFIG['coingecko']['base_url']}/coins/{crypto_id}/market_chart"
            params = {"vs_currency": "usd", "days": request_days, "interval": "daily"}
            
            print(f"{Fore.CYAN}   🌐 Solicitando {request_days} días de datos de CoinGecko...")
            
            response = requests.get(url, params=params, timeout=API_CONFIG['coingecko']['timeout'])
            response.raise_for_status()
            
            data = response.json()
            prices = data.get("prices", [])
            volumes = data.get("total_volumes", [])
            
            if not prices:
                print(f"{Fore.RED}   ❌ No se recibieron datos de precios")
                return None
            
            print(f"{Fore.GREEN}   ✅ Recibidos {len(prices)} puntos de datos")
            
            df = pd.DataFrame(prices, columns=["timestamp", "price"])
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            
            if volumes:
                vol_df = pd.DataFrame(volumes, columns=["timestamp", "volume"])
                vol_df["timestamp"] = pd.to_datetime(vol_df["timestamp"], unit="ms")
                df = df.merge(vol_df, on="timestamp", how="left")
            else:
                df["volume"] = 0
            
            # Limpiar datos
            df = df.dropna(subset=['price'])
            df = df[df['price'] > 0]  # Eliminar precios = 0
            
            df.set_index("timestamp", inplace=True)
            df = df.sort_index()
            
            print(f"{Fore.GREEN}   ✅ DataFrame procesado: {len(df)} filas válidas")
            return df
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Error CoinGecko para {crypto_id}: {e}")
            return None
    
    def _get_from_cryptocompare(self, crypto_symbol, days=90):
        """Obtiene datos de CryptoCompare - VERSIÓN MEJORADA"""
        try:
            # Solicitar más días para asegurar suficientes datos
            request_days = max(days, 200)  # Mínimo 200 días
            
            url = f"{API_CONFIG['cryptocompare']['base_url']}/histoday"
            params = {
                "fsym": crypto_symbol,
                "tsym": "USD",
                "limit": request_days,
                "aggregate": 1
            }
            
            print(f"{Fore.CYAN}   🌐 Solicitando {request_days} días de datos de CryptoCompare...")
            
            response = requests.get(url, params=params, timeout=API_CONFIG['cryptocompare']['timeout'])
            response.raise_for_status()
            
            data = response.json()
            if data.get("Response") == "Error":
                print(f"{Fore.RED}   ❌ Error de API: {data.get('Message', 'Desconocido')}")
                return None
            
            hist_data = data.get("Data", {}).get("Data", [])
            if not hist_data:
                print(f"{Fore.RED}   ❌ No se recibieron datos históricos")
                return None
            
            print(f"{Fore.GREEN}   ✅ Recibidos {len(hist_data)} puntos de datos")
            
            df_data = []
            for item in hist_data:
                if item.get("close", 0) > 0:  # Solo precios válidos
                    df_data.append({
                        "timestamp": pd.to_datetime(item["time"], unit="s"),
                        "price": float(item["close"]),
                        "volume": float(item.get("volumeto", 0))
                    })
            
            if not df_data:
                print(f"{Fore.RED}   ❌ No hay datos válidos después del procesamiento")
                return None
            
            df = pd.DataFrame(df_data)
            df.set_index("timestamp", inplace=True)
            df = df.sort_index()
            
            print(f"{Fore.GREEN}   ✅ DataFrame procesado: {len(df)} filas válidas")
            return df
            
        except Exception as e:
            print(f"{Fore.RED}   ❌ Error CryptoCompare para {crypto_symbol}: {e}")
            return None
    
    def _get_from_coincap(self, crypto_id, days=90):
        """Obtiene datos de CoinCap"""
        try:
            # CoinCap no tiene datos históricos tan detallados, solo precio actual
            url = f"{API_CONFIG['coincap']['base_url']}/assets/{crypto_id}"
            
            response = requests.get(url, timeout=API_CONFIG['coincap']['timeout'])
            response.raise_for_status()
            
            data = response.json().get("data", {})
            if not data:
                return None
            
            # Crear DataFrame básico con precio actual
            current_price = float(data.get("priceUsd", 0))
            if current_price == 0:
                return None
                
            # Generar datos simulados para análisis (solo como respaldo)
            dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
            df = pd.DataFrame({
                'price': [current_price] * days,  # Precio constante (limitación)
                'volume': [0] * days
            }, index=dates)
            
            return df
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error CoinCap para {crypto_id}: {e}")
            return None
    
    def get_crypto_data(self, crypto_name, days=90):
        """Obtiene datos con sistema de failover - VERSIÓN MEJORADA"""
        cache_key = self._get_cache_key(crypto_name, 'daily', days)
        
        # Verificar cache
        if self._is_cache_valid(cache_key):
            print(f"{Fore.YELLOW}📦 Usando cache para {crypto_name}")
            return self.cache[cache_key]['data']
        
        crypto_config = CRYPTO_CONFIG.get(crypto_name, {})
        df = None
        
        # Intentar APIs en orden de prioridad
        print(f"{Fore.BLUE}🔄 Intentando obtener datos para {crypto_name}...")
        
        if self.api_status.get('coingecko', False):
            print(f"{Fore.CYAN}   Probando CoinGecko...")
            df = self._get_from_coingecko(crypto_config.get('coingecko'), days)
            if df is not None:
                print(f"{Fore.GREEN}✅ Datos obtenidos de CoinGecko para {crypto_name}")
                self.debug_data_quality(df, crypto_name)
        
        if df is None and self.api_status.get('cryptocompare', False):
            print(f"{Fore.CYAN}   Probando CryptoCompare...")
            df = self._get_from_cryptocompare(crypto_config.get('cryptocompare'), days)
            if df is not None:
                print(f"{Fore.GREEN}✅ Datos obtenidos de CryptoCompare para {crypto_name}")
                self.debug_data_quality(df, crypto_name)
        
        if df is None and self.api_status.get('coincap', False):
            print(f"{Fore.CYAN}   Probando CoinCap...")
            df = self._get_from_coincap(crypto_config.get('coincap'), days)
            if df is not None:
                print(f"{Fore.YELLOW}⚠️  Datos básicos obtenidos de CoinCap para {crypto_name}")
                self.debug_data_quality(df, crypto_name)
        
        if df is not None:
            # Verificar que tenemos suficientes datos
            if len(df) < 200:
                print(f"{Fore.YELLOW}⚠️  Solo {len(df)} días de datos para {crypto_name} (se necesitan 200 para MA200)")
            
            # Guardar en cache
            self.cache[cache_key] = {
                'data': df,
                'timestamp': datetime.now()
            }
        else:
            print(f"{Fore.RED}❌ No se pudieron obtener datos para {crypto_name}")
        
        return df
    
    def debug_data_quality(self, df, crypto_name):
        """Función de diagnóstico para verificar calidad de datos"""
        print(f"\n{Fore.YELLOW}🔍 DIAGNÓSTICO PARA {crypto_name}:")
        
        if df is None:
            print(f"{Fore.RED}❌ DataFrame es None")
            return False
        
        print(f"{Fore.BLUE}📊 Información básica:")
        print(f"   - Filas totales: {len(df)}")
        print(f"   - Columnas: {list(df.columns)}")
        print(f"   - Rango de fechas: {df.index.min()} a {df.index.max()}")
        
        if 'price' not in df.columns:
            print(f"{Fore.RED}❌ No existe columna 'price'")
            return False
        
        print(f"   - Precios válidos: {df['price'].notna().sum()}/{len(df)}")
        print(f"   - Precio mín: ${df['price'].min():.2f}")
        print(f"   - Precio máx: ${df['price'].max():.2f}")
        print(f"   - Precio actual: ${df['price'].iloc[-1]:.2f}")
        
        # Verificar MAs si existen
        for ma in ['MA9', 'MA21', 'MA50', 'MA200']:
            if ma in df.columns:
                valid_count = df[ma].notna().sum()
                print(f"   - {ma}: {valid_count}/{len(df)} valores válidos")
                if valid_count > 0:
                    print(f"     Último valor: ${df[ma].iloc[-1]:.2f}" if not pd.isna(df[ma].iloc[-1]) else "     Último valor: N/A")
        
        return True
    
    def detect_golden_death_cross(self, df):
        """Detecta Golden Cross y Death Cross - VERSIÓN FINAL"""
        if df is None:
            return {"status": "Error", "days_since": 0, "description": "Sin datos"}
        
        try:
            print(f"{Fore.BLUE}🔍 Analizando cruces Golden/Death...")
            
            # Verificar que tenemos las columnas necesarias
            if 'MA50' not in df.columns or 'MA200' not in df.columns:
                print(f"{Fore.RED}❌ Faltan columnas MA50 o MA200")
                return {"status": "Error", "days_since": 0, "description": "Faltan columnas MA50 o MA200"}
            
            # Filtrar datos válidos
            valid_data = df.dropna(subset=['MA50', 'MA200'])
            
            if len(valid_data) < 2:
                print(f"{Fore.RED}❌ Insuficientes datos válidos para análisis de cruces")
                return {"status": "Sin datos", "days_since": 0, "description": "Datos insuficientes para cruces"}
            
            print(f"   📊 Datos válidos para cruces: {len(valid_data)}")
            
            # Usar hasta 60 días para detectar cruces (más amplio)
            recent_data = valid_data.tail(min(60, len(valid_data)))
            
            if len(recent_data) < 2:
                return {"status": "Sin datos", "days_since": 0, "description": "Datos insuficientes"}
            
            ma50 = recent_data['MA50'].values
            ma200 = recent_data['MA200'].values
            
            print(f"   📈 Analizando {len(ma50)} puntos de datos recientes")
            print(f"   📊 MA50 actual: ${ma50[-1]:.2f}")
            print(f"   📊 MA200 actual: ${ma200[-1]:.2f}")
            
            # Detectar cruces recientes
            cross_up = False
            cross_down = False
            cross_day = 0
            
            # Revisar desde el más reciente hacia atrás
            for i in range(len(ma50)-1, 0, -1):
                # Golden Cross: MA50 cruza por encima de MA200
                if ma50[i-1] <= ma200[i-1] and ma50[i] > ma200[i]:
                    cross_up = True
                    cross_day = len(ma50) - i
                    print(f"   🟢 Golden Cross detectado hace {cross_day} días")
                    break
                # Death Cross: MA50 cruza por debajo de MA200
                elif ma50[i-1] >= ma200[i-1] and ma50[i] < ma200[i]:
                    cross_down = True
                    cross_day = len(ma50) - i
                    print(f"   🔴 Death Cross detectado hace {cross_day} días")
                    break
            
            if cross_up:
                return {"status": "Golden Cross", "days_since": cross_day, "description": f"Golden Cross hace {cross_day} días"}
            elif cross_down:
                return {"status": "Death Cross", "days_since": cross_day, "description": f"Death Cross hace {cross_day} días"}
            else:
                # Verificar estado actual
                current_ma50 = ma50[-1]
                current_ma200 = ma200[-1]
                
                # Calcular la diferencia porcentual
                diff_pct = ((current_ma50 - current_ma200) / current_ma200) * 100
                
                if current_ma50 > current_ma200:
                    print(f"   📊 MA50 está {diff_pct:.1f}% por encima de MA200")
                    return {"status": "MA50 > MA200", "days_since": 0, "description": f"MA50 {diff_pct:.1f}% por encima"}
                else:
                    print(f"   📊 MA50 está {abs(diff_pct):.1f}% por debajo de MA200")
                    return {"status": "MA50 < MA200", "days_since": 0, "description": f"MA50 {abs(diff_pct):.1f}% por debajo"}
                    
        except Exception as e:
            print(f"{Fore.RED}❌ Error analizando cruces: {e}")
            import traceback
            traceback.print_exc()
            return {"status": "Error", "days_since": 0, "description": f"Error: {str(e)}"}

    def calculate_technical_indicators(self, df):
        """Calcula todos los indicadores técnicos - VERSIÓN ULTRA MEJORADA"""
        if df is None:
            print(f"{Fore.RED}❌ DataFrame es None")
            return None
        
        if len(df) < 200:
            print(f"{Fore.YELLOW}⚠️  Solo {len(df)} días de datos (se recomiendan 200+ para MA200)")
            # Continuar con menos datos pero ajustar ventanas
        
        try:
            print(f"{Fore.BLUE}🔄 Calculando indicadores técnicos...")
            
            # Asegurar que tenemos la columna price
            if 'price' not in df.columns:
                print(f"{Fore.RED}❌ Error: No se encontró columna 'price'")
                return None
            
            # Verificar datos válidos
            valid_prices = df['price'].notna().sum()
            print(f"   📊 Precios válidos: {valid_prices}/{len(df)}")
            
            if valid_prices < 50:
                print(f"{Fore.RED}❌ Insuficientes precios válidos para análisis")
                return None
            
            # Calcular medias móviles con manejo de datos limitados
            min_periods_9 = min(9, len(df))
            min_periods_21 = min(21, len(df))
            min_periods_50 = min(50, len(df))
            min_periods_200 = min(200, len(df))
            
            df['MA9'] = df['price'].rolling(window=9, min_periods=min_periods_9).mean()
            df['MA21'] = df['price'].rolling(window=21, min_periods=min_periods_21).mean()
            df['MA50'] = df['price'].rolling(window=50, min_periods=min_periods_50).mean()
            df['MA200'] = df['price'].rolling(window=200, min_periods=min_periods_200).mean()
            
            # Verificar que se calcularon correctamente
            ma_stats = {}
            for ma_name in ['MA9', 'MA21', 'MA50', 'MA200']:
                valid_count = df[ma_name].notna().sum()
                ma_stats[ma_name] = valid_count
                print(f"   📈 {ma_name}: {valid_count}/{len(df)} valores calculados")
            
            # Solo continuar si tenemos al menos MA50 y MA200
            if ma_stats['MA50'] == 0 or ma_stats['MA200'] == 0:
                print(f"{Fore.RED}❌ No se pudieron calcular MA50 o MA200")
                return None
            
            # Pendientes de las medias móviles
            df['MA9_slope'] = df['MA9'].diff()
            df['MA21_slope'] = df['MA21'].diff()
            df['MA50_slope'] = df['MA50'].diff()
            df['MA200_slope'] = df['MA200'].diff()
            
            # RSI
            try:
                df['RSI'] = ta.momentum.RSIIndicator(df['price'], window=14).rsi()
                rsi_count = df['RSI'].notna().sum()
                print(f"   📊 RSI: {rsi_count}/{len(df)} valores calculados")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Error calculando RSI: {e}")
                df['RSI'] = np.nan
            
            # MACD
            try:
                macd_indicator = ta.trend.MACD(df['price'])
                df['MACD'] = macd_indicator.macd()
                df['MACD_signal'] = macd_indicator.macd_signal()
                df['MACD_histogram'] = macd_indicator.macd_diff()
                
                macd_count = df['MACD'].notna().sum()
                print(f"   📈 MACD: {macd_count}/{len(df)} valores calculados")
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Error calculando MACD: {e}")
                df['MACD'] = np.nan
                df['MACD_signal'] = np.nan
                df['MACD_histogram'] = np.nan
            
            # Pendientes del MACD
            df['MACD_slope'] = df['MACD'].diff()
            df['MACD_signal_slope'] = df['MACD_signal'].diff()
            
            # Bollinger Bands
            try:
                bollinger = ta.volatility.BollingerBands(df['price'])
                df['BB_upper'] = bollinger.bollinger_hband()
                df['BB_middle'] = bollinger.bollinger_mavg()
                df['BB_lower'] = bollinger.bollinger_lband()
            except Exception as e:
                print(f"{Fore.YELLOW}⚠️  Error calculando Bollinger Bands: {e}")
            
            # Mostrar últimos valores para debug
            if len(df) > 0:
                last_row = df.iloc[-1]
                print(f"{Fore.CYAN}   📋 Últimos valores:")
                print(f"      Precio: ${last_row['price']:.2f}")
                
                if not pd.isna(last_row['MA50']):
                    print(f"      MA50: ${last_row['MA50']:.2f}")
                else:
                    print(f"      MA50: N/A")
                    
                if not pd.isna(last_row['MA200']):
                    print(f"      MA200: ${last_row['MA200']:.2f}")
                else:
                    print(f"      MA200: N/A")
                    
                if not pd.isna(last_row['RSI']):
                    print(f"      RSI: {last_row['RSI']:.1f}")
                else:
                    print(f"      RSI: N/A")
            
            print(f"{Fore.GREEN}✅ Indicadores calculados correctamente")
            return df
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error calculando indicadores: {e}")
            import traceback
            traceback.print_exc()
            return None

    def analyze_ma_alignment(self, df):
        """Analiza el orden de las medias móviles - VERSIÓN MEJORADA"""
        if df is None:
            return {"status": "Error", "score": 0, "description": "Sin datos"}
        
        try:
            # Filtrar datos válidos
            valid_data = df.dropna(subset=['MA9', 'MA21', 'MA50', 'MA200'])
            
            if len(valid_data) == 0:
                return {"status": "Sin datos", "score": 0, "description": "MAs no calculadas"}
            
            last_row = valid_data.iloc[-1]
            mas = [last_row['MA9'], last_row['MA21'], last_row['MA50'], last_row['MA200']]
            
            # Verificar que todas las MAs están disponibles
            if any(pd.isna(mas)):
                available_mas = []
                if not pd.isna(last_row['MA9']): available_mas.append('MA9')
                if not pd.isna(last_row['MA21']): available_mas.append('MA21')
                if not pd.isna(last_row['MA50']): available_mas.append('MA50')
                if not pd.isna(last_row['MA200']): available_mas.append('MA200')
                
                return {"status": "Parcial", "score": 0, "description": f"Solo disponibles: {', '.join(available_mas)}"}
            
            # Verificar orden alcista (9>21>50>200)
            bullish_order = all(mas[i] > mas[i+1] for i in range(len(mas)-1))
            
            # Verificar orden bajista (9<21<50<200)
            bearish_order = all(mas[i] < mas[i+1] for i in range(len(mas)-1))
            
            if bullish_order:
                return {"status": "Alcista Fuerte", "score": 4, "description": "MA9>MA21>MA50>MA200"}
            elif bearish_order:
                return {"status": "Bajista Fuerte", "score": -4, "description": "MA9<MA21<MA50<MA200"}
            else:
                # Contar cuántas están en orden
                bullish_count = sum(1 for i in range(len(mas)-1) if mas[i] > mas[i+1])
                score = bullish_count - (len(mas)-1-bullish_count)
                
                if score > 0:
                    return {"status": "Alcista Parcial", "score": score, "description": f"{bullish_count}/{len(mas)-1} cruces alcistas"}
                elif score < 0:
                    return {"status": "Bajista Parcial", "score": score, "description": f"{len(mas)-1-bullish_count}/{len(mas)-1} cruces bajistas"}
                else:
                    return {"status": "Lateral", "score": 0, "description": "MAs mezcladas"}
                    
        except Exception as e:
            return {"status": "Error", "score": 0, "description": f"Error: {str(e)}"}
    
    def detect_divergences(self, df):
        """Detecta divergencias básicas"""
        if df is None:
            return {"rsi_divergence": "Sin datos", "macd_divergence": "Sin datos"}
        
        try:
            # Últimos 20 días para análisis
            recent_data = df.dropna().tail(20)
            
            if len(recent_data) < 10:
                return {"rsi_divergence": "Datos insuficientes", "macd_divergence": "Datos insuficientes"}
            
            prices = recent_data['price'].values
            rsi = recent_data['RSI'].values
            macd = recent_data['MACD'].values
            
            # Análisis simplificado de divergencias
            price_trend = prices[-1] - prices[0]
            rsi_trend = rsi[-1] - rsi[0]
            macd_trend = macd[-1] - macd[0]
            
            # Detectar divergencias
            rsi_div = "Normal"
            macd_div = "Normal"
            
            if price_trend > 0 and rsi_trend < 0:
                rsi_div = "Divergencia Bajista"
            elif price_trend < 0 and rsi_trend > 0:
                rsi_div = "Divergencia Alcista"
            
            if price_trend > 0 and macd_trend < 0:
                macd_div = "Divergencia Bajista"
            elif price_trend < 0 and macd_trend > 0:
                macd_div = "Divergencia Alcista"
            
            return {"rsi_divergence": rsi_div, "macd_divergence": macd_div}
            
        except Exception as e:
            return {"rsi_divergence": "Error", "macd_divergence": "Error"}
    
    def get_trading_signals(self, df):
        """Genera señales de trading consolidadas"""
        if df is None:
            return {"signal": "Error", "score": 0, "confidence": 0, "description": "Sin datos"}
        
        try:
            last_row = df.dropna().iloc[-1]
            
            # Análisis de componentes
            ma_analysis = self.analyze_ma_alignment(df)
            cross_analysis = self.detect_golden_death_cross(df)
            divergences = self.detect_divergences(df)
            
            # RSI
            rsi = last_row['RSI']
            rsi_signal = 1 if rsi < 30 else -1 if rsi > 70 else 0
            
            # MACD
            macd = last_row['MACD']
            macd_signal = last_row['MACD_signal']
            macd_cross = 1 if macd > macd_signal else -1 if macd < macd_signal else 0
            
            # Pendientes
            macd_slope = last_row['MACD_slope']
            ma9_slope = last_row['MA9_slope']
            
            slope_signal = 0
            if not pd.isna(macd_slope) and not pd.isna(ma9_slope):
                slope_signal = 1 if (macd_slope > 0 and ma9_slope > 0) else -1 if (macd_slope < 0 and ma9_slope < 0) else 0
            
            # Calcular score total
            total_score = (
                ma_analysis['score'] * 0.3 +
                rsi_signal * 0.2 +
                macd_cross * 0.2 +
                slope_signal * 0.15 +
                (1 if cross_analysis['status'] == 'Golden Cross' else -1 if cross_analysis['status'] == 'Death Cross' else 0) * 0.15
            )
            
            # Determinar señal
            if total_score > 1.5:
                signal = "COMPRA FUERTE"
                confidence = min(int(abs(total_score) * 20), 100)
            elif total_score > 0.5:
                signal = "COMPRA"
                confidence = min(int(abs(total_score) * 25), 100)
            elif total_score < -1.5:
                signal = "VENTA FUERTE"
                confidence = min(int(abs(total_score) * 20), 100)
            elif total_score < -0.5:
                signal = "VENTA"
                confidence = min(int(abs(total_score) * 25), 100)
            else:
                signal = "NEUTRO"
                confidence = 0
            
            return {
                "signal": signal,
                "score": round(total_score, 2),
                "confidence": confidence,
                "description": f"RSI:{rsi:.1f} MACD:{macd_cross} MA:{ma_analysis['status']}",
                "components": {
                    "ma_analysis": ma_analysis,
                    "cross_analysis": cross_analysis,
                    "divergences": divergences,
                    "rsi": rsi,
                    "macd_cross": macd_cross
                }
            }
            
        except Exception as e:
            return {"signal": "Error", "score": 0, "confidence": 0, "description": f"Error: {e}"}
    
    def format_signal_display(self, signal_data):
        """Formatea la señal para mostrar con colores"""
        signal = signal_data["signal"]
        confidence = signal_data["confidence"]
        
        if "COMPRA" in signal:
            if "FUERTE" in signal:
                return f"{Fore.GREEN}🚀 {signal} ({confidence}%){Style.RESET_ALL}"
            else:
                return f"{Fore.GREEN}📈 {signal} ({confidence}%){Style.RESET_ALL}"
        elif "VENTA" in signal:
            if "FUERTE" in signal:
                return f"{Fore.RED}💥 {signal} ({confidence}%){Style.RESET_ALL}"
            else:
                return f"{Fore.RED}📉 {signal} ({confidence}%){Style.RESET_ALL}"
        else:
            return f"{Fore.YELLOW}⚪ {signal}{Style.RESET_ALL}"

def main():
    print(f"{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}🚀 ANALIZADOR CRYPTO - FASE 1 COMPLETA")
    print(f"{Fore.CYAN}📊 Análisis Técnico Avanzado Multi-API")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    
    analyzer = CryptoAnalyzer()
    
    print(f"\n{Fore.BLUE}🔄 Iniciando análisis completo...{Style.RESET_ALL}")
    
    tabla_principal = []
    tabla_detallada = []
    
    for crypto_name in CRYPTO_CONFIG.keys():
        print(f"\n{Fore.MAGENTA}📊 Analizando {crypto_name}...{Style.RESET_ALL}")
        
        try:
            # Obtener datos
            df = analyzer.get_crypto_data(crypto_name, days=200)
            
            if df is None:
                tabla_principal.append([crypto_name, "❌ Sin datos", "❌ Error", "❌ Error"])
                continue
            
            # Calcular indicadores
            df = analyzer.calculate_technical_indicators(df)
            
            if df is None:
                tabla_principal.append([crypto_name, "❌ Error cálculo", "❌ Error", "❌ Error"])
                continue
            
            # Obtener señales
            signals = analyzer.get_trading_signals(df)
            
            # Precio actual
            current_price = df['price'].iloc[-1]
            
            # Análisis detallado
            ma_analysis = analyzer.analyze_ma_alignment(df)
            cross_analysis = analyzer.detect_golden_death_cross(df)
            
            # Tabla principal
            signal_display = analyzer.format_signal_display(signals)
            tabla_principal.append([
                crypto_name,
                f"${current_price:,.2f}",
                signal_display,
                f"{signals['score']:.2f}"
            ])
            
            # Tabla detallada
            tabla_detallada.append([
                crypto_name,
                ma_analysis['status'],
                cross_analysis['status'],
                f"{df['RSI'].iloc[-1]:.1f}",
                f"{df['MACD'].iloc[-1]:.4f}",
                signals['description']
            ])
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error procesando {crypto_name}: {e}")
            tabla_principal.append([crypto_name, "❌ Error", "❌ Error", "❌ Error"])
        
        # Pausa para evitar rate limiting
        time.sleep(1.5)
    
    # Mostrar resultados
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}📈 RESUMEN EJECUTIVO")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    
    print(tabulate(tabla_principal, 
                   headers=["Crypto", "Precio USD", "Señal", "Score"], 
                   tablefmt="fancy_grid"))
    
    print(f"\n{Fore.CYAN}{'='*80}")
    print(f"{Fore.CYAN}🔍 ANÁLISIS DETALLADO")
    print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}")
    
    print(tabulate(tabla_detallada, 
                   headers=["Crypto", "MAs", "Cross", "RSI", "MACD", "Detalles"], 
                   tablefmt="fancy_grid"))
    
    # Leyenda
    print(f"\n{Fore.CYAN}📋 LEYENDA:")
    print(f"{Fore.GREEN}🚀 COMPRA FUERTE: Alta confluencia alcista")
    print(f"{Fore.GREEN}📈 COMPRA: Señal alcista moderada")
    print(f"{Fore.RED}💥 VENTA FUERTE: Alta confluencia bajista")
    print(f"{Fore.RED}📉 VENTA: Señal bajista moderada")
    print(f"{Fore.YELLOW}⚪ NEUTRO: Sin señal clara")
    print(f"{Style.RESET_ALL}")
    
    print(f"{Fore.MAGENTA}💡 COMPONENTES DEL ANÁLISIS:")
    print(f"{Fore.MAGENTA}• MAs: Orden de medias móviles 9,21,50,200")
    print(f"{Fore.MAGENTA}• Cross: Golden Cross / Death Cross")
    print(f"{Fore.MAGENTA}• RSI: Índice de Fuerza Relativa")
    print(f"{Fore.MAGENTA}• MACD: Convergencia/Divergencia de Medias")
    print(f"{Fore.MAGENTA}• Score: Puntuación de confluencia (-4 a +4)")
    print(f"{Style.RESET_ALL}")

if __name__ == "__main__":
    main()

# Editado desde Codespace el 13/07
