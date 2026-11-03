"""Biblioteca própria do projeto.

Regra de dependência: etl, ml e app importam de tools; tools não importa de nenhum deles.
Evite imports pesados no topo dos módulos usados pelo app (a imagem Docker só tem o grupo `app`).
"""
