#include <bits/stdc++.h>
using namespace std;
int n;

struct TCar
{
    int id;
    int numb;
    pair<int, int> road[105];
} car[101]; // gia su toi da co 100 xe

vector<pair<int, int>> ngatu[101][101];
set<int> q4[101][101];

set<pair<int, int>> idngatu;

bool cmp(TCar A, TCar B)
{
    return A.id < B.id;
}

string s;

int main(int argc, char* argv[])
{
    //freopen("A.inp", "r", stdin);
    //freopen("A.out", "w", stdout);
    std::ifstream infile(argv[1]);
    std::string line;
    std::map<std::pair<int, int>, int> dataMap;
    
    while (std::getline(infile, line)) {
        if (line[0] == 'a') {
            std::istringstream iss(line);
            char a;
            int X, Y, U, V;
            iss >> a >> X >> Y >> U >> V;
            dataMap[std::make_pair(X, Y)] = U;
        }
    }

    cin >> n;

    int pre = 100;
    int x, y, m, cur;

    getline(cin, s);

    int cnt = 0;
    int type;

    while(getline(cin, s))
    {
        int len = s.length();
        int tmp = 0;
        int res = 0;
        bool ok = 0;
        for(int i = 0; i < len; i++)
        {
            if(s[i] == ' ')
            {
                ok = 1;
                continue;
            }
            if(ok)
                tmp = tmp*10 + (s[i] - '0');
            else
                res = res*10 + (s[i] - '0');
        }
        if(!ok)
        {
            if(cnt == n)
            {
                type = res;
                break;
            }
            car[++cnt].id = res;
            car[cnt].numb = 0;
        }
        else
        {
            car[cnt].numb++;
            car[cnt].road[car[cnt].numb] = make_pair(res, tmp);
        }
    }

    sort(car+1, car+1+n, cmp);   // sap xep xe theo id

    for(int i = 1; i <= n; i++)   // ghi nhan cac cap nga tu
    {
        int sl = car[i].numb;
        for(int j = 2; j <= sl; j++)
        {
            if(car[i].road[j].first != car[i].road[j-1].first)
            {
                q4[car[i].road[j-1].first][car[i].road[j].first].insert(i); // xe i đi qua ngã tư j-1->j
                ngatu[car[i].road[j-1].first][car[i].road[j].first].push_back(make_pair(car[i].road[j-1].second, car[i].road[j].second));
                idngatu.insert(make_pair(car[i].road[j-1].first, car[i].road[j].first));  // ghi lai cac cap nga tu tranh trung lap
            }
        }
    }

    type = 5;
    {
        if(type == 0)
        {
            for(int i = 1; i <= n; i++)
            {
                int j = car[i].numb;
                cout << car[i].road[j].first << " ";
            }
            cout << '\n';
        }
        if(type == 1)
        {
            for(int i = 1; i <= n; i++)
            {
                int j = car[i].numb;
                cout << car[i].road[j].second << " ";
            }
            cout << '\n';
        }
        if(type == 2)
        {
            for(int i = 1; i <= n; i++)
            {
                cout << car[i].road[1].first << " ";
            }
            cout << '\n';
        }
        if(type == 3)
        {
            for(int i = 1; i <= n; i++)
            {
                bool ok = 0;
                int waitTime = 0;
                int sl = car[i].numb;
                int tmp = car[i].road[1].first;

                for(int j = 2; j <= sl; j++)
                {
                    if(car[i].road[j].first == tmp)
                    {
                         waitTime += car[i].road[j].second - car[i].road[j-1].second;
                    }
                    else
                    {
                        if(waitTime != 0)
                        {
                            ok = 1;
                            cout << tmp << "(" << waitTime << ")" << " ";
                        }
                        waitTime = 0;
                        tmp = car[i].road[j].first;
                    }

                }
                if(ok == 0)
                    cout << -1;
                cout << '\n';
            }
        }
        if(type == 4)
        {
            bool ok = 0;
            for(auto k: idngatu)
            {
                if(q4[k.first][k.second].size() > 1)
                {
                    ok = 1;
                    cout << k.first << "-" << k.second << " ";
                }
            }
            if(!ok)
                cout << 0;
            cout << '\n';
        }
        if(type == 5)
        {
            bool ok = 0;
            for(auto k: idngatu)
            {
                if(ngatu[k.first][k.second].size() > 
                        dataMap[std::make_pair(k.first, k.second)]){
                    cout << 1 << '\n';  
                    return 0;
                }
                        
                for(int i = 0; i < ngatu[k.first][k.second].size(); i++)
                {
                    for(int j = i+1; j < ngatu[k.first][k.second].size(); j++)
                    {
                        int tAs = ngatu[k.first][k.second][i].first;
                        int tAt = ngatu[k.first][k.second][i].second;
                        int tBs = ngatu[k.first][k.second][j].first;
                        int tBt = ngatu[k.first][k.second][j].second;
                        if((tAs < tBs && tAt > tBt) || (tAs > tBs && tAt < tBt))
                        {
                            ok = 1;
                            break;
                        }
                    }
                    if(ok) break;
                }
                if(ok) break;
            }
            cout << ok << '\n';
        }
    }
    return 0;

}
