import sched
import time
import random


class Hero:
    def __init__(self, name, hp, hp_regen, mana, mana_regen, dmg, stren, agi, intel, str_growth, agi_growth,
                 int_growth, a_s, bat, anim, armor, main_attr):
        self.name = name
        self._hp = hp
        self._hp_regen = hp_regen
        self._mana = mana
        self._mana_regen = mana_regen
        self._dmg = dmg
        self._str = stren
        self._agi = agi
        self._int = intel
        self._str_growth = str_growth
        self._agi_growth = agi_growth
        self._int_growth = int_growth
        self._a_s = a_s
        self._bat = bat
        self._attack_point = anim
        self._armor = armor
        self._main_attr = main_attr

        self._level = 1
        self._magic_res = 0.25
        self._remaining_hp = self.max_hp()

    @property
    def remaining_hp(self):
        return self._remaining_hp

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value
        self._remaining_hp = self.max_hp()

    def max_hp(self):
        return self._hp + self.str() * 20

    def str(self):
        return self._str + self._str_growth * (self._level - 1)

    def agi(self):
        return self._agi + self._agi_growth * (self._level - 1)

    def int(self):
        return self._int + self._int_growth * (self._level - 1)

    def dmg(self):
        return random.randint(*self._dmg) + getattr(self, self._main_attr)()

    def a_s(self):
        return self._a_s + self.agi()

    def attack_point(self):
        return self._attack_point / (1 + self.a_s())

    def attack_time(self):
        return self._bat / (self.a_s() * 0.01)

    def attack(self):
        return self.attack_point(), self.dmg(), self.attack_time()

    def armor(self):
        return self._armor + 0.16 * self.agi()

    def dmg_multiplier(self):
        armor = self.armor()
        return 1 - ((0.052 * armor) / (0.9 + 0.048 * abs(armor)))

    def receive_dmg(self, dmg):
        reduced_dmg = dmg * self.dmg_multiplier()
        print(f'{self.name} receiving {reduced_dmg} damage.')
        self._remaining_hp -= reduced_dmg

    def regenerate_hp(self):
        max_hp = self.max_hp()
        if self._remaining_hp < max_hp:
            hp_regen = 0.1 * (self._hp_regen + 0.1 * self.str())
            self._remaining_hp = min(max_hp, self._remaining_hp + hp_regen)
            print(f'{self.name} regenerating {hp_regen} to {self._remaining_hp}.')


def sleep(secs):
    time.sleep(secs/1000)


class Simulation:
    def __init__(self, hero1, hero2):
        self.hero1 = hero1
        self.hero2 = hero2
        self.running = False
        self.scheduler = sched.scheduler(time.time, sleep)

    def receive_dmg(self, victim, dmg):
        if self.running:
            victim.receive_dmg(dmg)
            if victim.remaining_hp <= 0:
                print(f'{victim.name} died.')
                self.running = False

    def hero_attack(self, attacker, victim):
        if self.running:
            attack_point, dmg, next_attack = attacker.attack()
            print(attacker.name, 'attacks with', dmg)
            self.scheduler.enter(attack_point, 1, self.receive_dmg, (victim, dmg))
            self.scheduler.enter(next_attack, 1, self.hero_attack, (attacker, victim))

    def hp_regen(self, hero):
        if self.running:
            hero.regenerate_hp()
            self.scheduler.enter(0.1, 1, self.hp_regen, (hero, ))

    def run(self):
        self.running = True
        self.hp_regen(self.hero1)
        self.hp_regen(self.hero2)
        self.hero_attack(self.hero1, self.hero2)
        self.hero_attack(self.hero2, self.hero1)
        self.scheduler.run()


def main():
    # jug = Hero('Juggernaut', 200, 0.5, 75, 0, [16, 20], 20, 34, 14, 2.2, 2.8, 1.4, 110, 1.4, 0.33, 0, 'agi')
    # void = Hero('Faceless void', 200, 0.5, 75, 0, [33, 39], 24, 23, 15, 2.4, 3, 1.5, 100, 1.7, 0.5, 0, 'agi')
    # ck = Hero('Chaos knight', 200, 0, 75, 0, [29, 59], 22, 14, 18, 3.4, 1.4, 1.2, 100, 1.7, 0.5, 1, 'str')
    ogre = Hero('Ogre magi', 200, 3.25, 75, 0, [39, 45], 23, 14, 15, 3.5, 1.9, 2.5, 100, 1.7, 0.3, 5, 'int')
    ogre_items = Hero('Ogre magi', 200, 3.25, 75, 0, [39, 45], 26, 17, 18, 3.5, 1.9, 2.5, 100, 1.7, 0.3, 5, 'int')
    # terrorblade = Hero('Terrorblade', 200, 0, 75, 0, [26, 32], 15, 22, 19, 1.7, 4.8, 1.6, 100, 1.5, 0.3, 7, 'agi')

    # jug_items = Hero('Juggernaut_items', 200, 0.5, 75, 0, [16, 20], 24, 38, 18, 2.2, 2.8, 1.4, 110, 1.4, 0.33, 0, 'agi')
    # jug.level = 30
    # terrorblade.level = 30
    # void.level = 30

    sim = Simulation(ogre, ogre_items)
    sim.run()


if __name__ == '__main__':
    main()
